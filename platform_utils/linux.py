"""Implementación para Linux (X11 y Wayland)."""
from __future__ import annotations

import os
import subprocess
from typing import Optional

from .base import (
    ActiveWindow,
    PlatformNotSupportedError,
    WindowDetectionError,
    WindowProvider,
)

try:
    from Xlib import display
    from Xlib.ext import screensaver
    import ewmh
    X11_AVAILABLE = True
except ImportError:
    X11_AVAILABLE = False


class LinuxProvider(WindowProvider):
    platform_id = "linux"

    def __init__(self) -> None:
        self.session_type = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()
        self._display = None
        self._ewmh = None

        if self.session_type == "x11":
            if not X11_AVAILABLE:
                raise PlatformNotSupportedError(
                    "Faltan dependencias (python-xlib, ewmh) para X11. "
                    "Ejecuta: pip install python-xlib ewmh"
                )
            self._init_x11()
        else:
            self.platform_id = f"linux-{self.session_type}"

    def _init_x11(self) -> None:
        try:
            self._display = display.Display()
            self._ewmh = ewmh.EWMH(self._display)
        except Exception as e:
            raise PlatformNotSupportedError(f"No se pudo conectar al servidor X11: {e}")

    def is_supported(self) -> tuple[bool, str]:
        if self.session_type == "x11":
            return True, "linux-x11 OK"
        elif self.session_type == "wayland":
            return False, (
                "Wayland detectado. Por seguridad, las apps no pueden leer "
                "la ventana activa. Se requiere X11 o permisos especiales."
            )
        return False, f"Entorno no soportado: {self.session_type}"

    def _get_process_name_by_pid(self, pid: int) -> str:
        """Respaldo: usa el comando 'ps' de Linux para obtener el nombre del proceso."""
        if not pid or pid <= 0:
            return "Desconocido"
        try:
            result = subprocess.check_output(
                ["ps", "-p", str(pid), "-o", "comm="],
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()
            if result:
                return result
        except Exception:
            pass
        return "Desconocido"

    def get_active_window(self) -> Optional[ActiveWindow]:
        if self.session_type == "wayland":
            return self._get_wayland_active_window()

        if not self._display or not self._ewmh:
            return None

        try:
            active_window = self._ewmh.getActiveWindow()
            if not active_window:
                return None

            # Obtener PID
            pid_prop = active_window.get_full_property(
                self._display.intern_atom("_NET_WM_PID"), 0
            )
            pid_value = pid_prop.value[0] if pid_prop else None

            # Obtener título (manejando bytes o str)
            window_name = active_window.get_wm_name()
            window_title = ""
            if isinstance(window_name, bytes):
                window_title = window_name.decode("utf-8", errors="ignore")
            elif isinstance(window_name, str):
                window_title = window_name

            # RESPALDO: Si el título está vacío, intentamos leer _NET_WM_NAME
            if not window_title:
                try:
                    title_prop = active_window.get_full_property(
                        self._display.intern_atom("_NET_WM_NAME"), 0
                    )
                    if title_prop:
                        window_title = title_prop.value.decode("utf-8", errors="ignore")
                except Exception:
                    pass

            process_name = "Desconocido"

            if pid_value:
                # 1. Intentamos con psutil primero
                try:
                    import psutil
                    process = psutil.Process(pid_value)
                    process_name = process.name()
                except Exception:
                    # 2. Si falla, usamos el comando 'ps'
                    process_name = self._get_process_name_by_pid(pid_value)

            # 🔥 PARCHE PARA BRAVE Y CHROMIUM
            # Si la ventana reporta un PID del sistema (como 2) o "Desconocido",
            # leemos la clase de la ventana (WM_CLASS) para identificar el navegador.
            if process_name in ["Kthreadd", "Desconocido", "kworker"] or (pid_value and pid_value <= 10):
                try:
                    wm_class = active_window.get_wm_class()
                    if wm_class:
                        class_str = str(wm_class).lower()
                        if "brave" in class_str:
                            process_name = "brave"
                        elif "chrome" in class_str:
                            process_name = "chrome"
                        elif "firefox" in class_str:
                            process_name = "firefox"
                except Exception:
                    pass

            app_name = process_name.replace(".exe", "").replace("-bin", "").capitalize()

            return ActiveWindow(
                process_name=process_name,
                app_name=app_name,
                pid=pid_value,
                window_title=window_title,
            )

        except Exception as e:
            raise WindowDetectionError(f"Error leyendo ventana en X11: {e}")

    def _get_wayland_active_window(self) -> Optional[ActiveWindow]:
        try:
            pid_str = subprocess.check_output(
                ["xdotool", "getactivewindow", "getwindowpid"], 
                stderr=subprocess.DEVNULL, text=True
            ).strip()
            
            if pid_str:
                pid = int(pid_str)
                process_name = self._get_process_name_by_pid(pid)
                return ActiveWindow(
                    process_name=process_name,
                    app_name=process_name.capitalize(),
                    pid=pid,
                    window_title="Ventana en Wayland"
                )
        except Exception:
            pass
        return None

    def get_idle_seconds(self) -> int:
        if self.session_type != "x11":
            return 0

        # Método 1: Usando XScreenSaver (el más preciso si está activo)
        if self._display:
            try:
                info = self._display.screensaver_query_info()
                if info and hasattr(info, 'idle') and info.idle > 0:
                    return info.idle
            except Exception:
                pass

        # Método 2: Respaldo usando xprintidle
        try:
            result = subprocess.check_output(["xprintidle"], text=True)
            idle_ms = int(result.strip())
            if idle_ms > 0:
                return idle_ms // 1000
        except Exception:
            pass

        # Método 3: Respaldo definitivo leyendo la posición del ratón
        # Si el sistema no nos da el idle, nosotros lo calculamos moviendo el ratón
        if self._display:
            try:
                import time
                
                # Obtenemos la posición actual del ratón
                root = self._display.screen().root
                pointer = root.query_pointer()
                current_pos = (pointer.root_x, pointer.root_y)
                
                # Si no tenemos una posición guardada, la guardamos
                if not hasattr(self, '_last_mouse_pos'):
                    self._last_mouse_pos = current_pos
                    self._last_mouse_time = time.time()
                    return 0
                
                # Si el ratón se movió, reseteamos el tiempo
                if current_pos != self._last_mouse_pos:
                    self._last_mouse_pos = current_pos
                    self._last_mouse_time = time.time()
                    return 0
                
                # Si no se movió, calculamos cuánto tiempo lleva quieto
                idle_time = int(time.time() - self._last_mouse_time)
                return idle_time
                
            except Exception:
                pass

        return 0

def create_provider() -> WindowProvider:
    return LinuxProvider()