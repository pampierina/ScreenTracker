"""
Interfaz base para detección de ventana activa e inactividad.

Define el contrato que cada plataforma (Linux, Windows, macOS) debe
implementar. El resto del proyecto solo importa estas clases y funciones,
nunca los módulos específicos de plataforma directamente.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Tipos de datos
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ActiveWindow:
    """
    Información de la ventana en primer plano.

    Attributes:
        process_name: Nombre del ejecutable (ej. "firefox", "code", "chrome.exe").
        app_name: Nombre "amigable" para mostrar en UI (ej. "Firefox").
        pid: ID del proceso dueño de la ventana (None si no se pudo obtener).
        window_title: Título de la ventana (puede ser None en Wayland).
    """
    process_name: str
    app_name: str
    pid: Optional[int] = None
    window_title: Optional[str] = None


# ---------------------------------------------------------------------------
# Excepciones
# ---------------------------------------------------------------------------

class PlatformNotSupportedError(RuntimeError):
    """La plataforma actual no está soportada o falta una dependencia."""


class WindowDetectionError(RuntimeError):
    """Falló la detección de la ventana activa en tiempo de ejecución."""


# ---------------------------------------------------------------------------
# Interfaz abstracta
# ---------------------------------------------------------------------------

class WindowProvider(ABC):
    """
    Proveedor de información del sistema operativo.

    Cada plataforma implementa esta clase. El resto del código trabaja
    únicamente contra esta interfaz.
    """

    #: Identificador legible de la plataforma ("linux-x11", "windows", ...)
    platform_id: str = "unknown"

    # ------------------------------------------------------------------
    # Ventana activa
    # ------------------------------------------------------------------
    @abstractmethod
    def get_active_window(self) -> Optional[ActiveWindow]:
        """
        Devuelve la ventana actualmente en primer plano.

        Retorna None si no se puede determinar (ej. escritorio sin ventanas,
        pantalla de bloqueo, o el usuario no tiene permisos).
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Inactividad
    # ------------------------------------------------------------------
    @abstractmethod
    def get_idle_seconds(self) -> int:
        """
        Segundos desde la última interacción del usuario (teclado/ratón).

        Retorna 0 si no se puede determinar.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Diagnóstico
    # ------------------------------------------------------------------
    def is_supported(self) -> tuple[bool, str]:
        """
        Indica si el proveedor puede operar en el entorno actual.

        Returns:
            (soportado, mensaje). Si no está soportado, el mensaje explica
            el motivo (útil para mostrar en UI o logs).
        """
        return True, f"{self.platform_id} OK"


# ---------------------------------------------------------------------------
# Selector de plataforma
# ---------------------------------------------------------------------------

_provider_instance: Optional[WindowProvider] = None


def get_provider() -> WindowProvider:
    """
    Devuelve la instancia única del proveedor para la plataforma actual.

    Selecciona automáticamente según sys.platform y, en Linux, según si
    la sesión es X11 o Wayland. Es lazy (solo importa el módulo la primera
    vez) para no cargar dependencias innecesarias.
    """
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    import sys

    if sys.platform == "linux":
        from . import linux as impl_module
    elif sys.platform == "win32":
        from . import windows as impl_module
    elif sys.platform == "darwin":
        from . import macos as impl_module
    else:
        raise PlatformNotSupportedError(f"Plataforma no soportada: {sys.platform}")

    _provider_instance = impl_module.create_provider()
    return _provider_instance


def reset_provider() -> None:
    """Útil en tests para forzar re-selección del proveedor."""
    global _provider_instance
    _provider_instance = None