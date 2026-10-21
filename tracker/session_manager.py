"""El motor de ScreenTracker: hilo que lee la ventana y acumula tiempo."""
from __future__ import annotations

import time
import threading
from datetime import datetime
from typing import Optional

from platform_utils import get_provider, ActiveWindow
from storage.database import Database

# Umbral de inactividad (en segundos). Si pasas de 120s sin tocar nada, se pausa.
IDLE_THRESHOLD = 120 

class Tracker:
    def __init__(self, db: Database) -> None:
        self.db = db
        self.provider = get_provider()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # Variables de estado interno
        self._current_app: Optional[str] = None
        self._current_pid: Optional[int] = None
        self._accumulated_seconds = 0
        self._session_start: datetime = datetime.now()

    def start(self) -> None:
        """Enciende el motor en un hilo aparte."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print("[Tracker] Motor iniciado.")

    def stop(self) -> None:
        """Apaga el motor y guarda lo último que quedó pendiente."""
        if not self._running:
            return
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        self._save_current_session()
        print("[Tracker] Motor detenido.")

    def _save_current_session(self) -> None:
        """Guarda en la BD los segundos acumulados de la app actual."""
        if self._current_app and self._accumulated_seconds > 0:
            self.db.insert_session(
                app_name=self._current_app,
                process_name=self._current_app.lower(),
                pid=self._current_pid or 0,
                start_time=self._session_start,
                duration_seconds=self._accumulated_seconds
            )
            # Reiniciamos el contador
            self._accumulated_seconds = 0
            self._session_start = datetime.now()

    def _run_loop(self) -> None:
        """El bucle principal que corre cada segundo."""
        while self._running:
            try:
                # 1. ¿El usuario apagó el tracking manualmente?
                if not self.db.get_tracking_enabled():
                    self._save_current_session() # Guardamos lo que llevábamos
                    self._current_app = None
                    time.sleep(1)
                    continue

                # 2. ¿El usuario está inactivo?
                idle_secs = self.provider.get_idle_seconds()
                if idle_secs > IDLE_THRESHOLD:
                    # Está inactivo. Guardamos lo que llevábamos y pausamos.
                    self._save_current_session()
                    self._current_app = None
                    time.sleep(1)
                    continue

                # 3. ¿Qué ventana está activa?
                window = self.provider.get_active_window()
                
                # Si por alguna razón no hay ventana (ej. pantalla de bloqueo), ignorar
                if not window or not window.pid:
                    time.sleep(1)
                    continue
                


                # 4. ¿Es la misma app que estábamos contando?
                if window.app_name == self._current_app:
                    # ¡Sí! Solo sumamos 1 segundo
                    self._accumulated_seconds += 1
                else:
                    # ¡Cambió de app! Guardamos la anterior y empezamos con la nueva
                    self._save_current_session()
                    self._current_app = window.app_name
                    self._current_pid = window.pid
                    self._accumulated_seconds = 1
                    self._session_start = datetime.now()

            except Exception as e:
                print(f"[Tracker] Error en el bucle: {e}")

            # Esperamos 1 segundo antes de volver a preguntar
            time.sleep(1)

    # Métodos para que la UI pueda consultar el estado actual en tiempo real
    def get_current_status(self) -> tuple[str, int]:
        return (self._current_app or "Ninguna", self._accumulated_seconds)