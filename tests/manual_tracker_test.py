"""Test para ver el Tracker en acción."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from storage.database import Database
from tracker.session_manager import Tracker

def main():
    db = Database()
    tracker = Tracker(db)
    
    # Nos aseguramos de que el tracking esté encendido en la BD
    db.set_tracking_enabled(True)
    
    print("\n--- Tracker en acción ---")
    print("Cambia entre ventanas (Brave, VS Code, Terminal) para ver cómo cambia el contador.")
    print("Si dejas de tocar el teclado por 2 minutos, el contador se detendrá.")
    print("Presiona Ctrl+C para detener.\n")
    
    tracker.start()
    
    try:
        while True:
            # Consultamos el estado en tiempo real para mostrarlo en pantalla
            app, secs = tracker.get_current_status()
            print(f"App actual: {app:<15} | Tiempo acumulado en esta sesión: {secs}s")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo tracker y guardando en la base de datos...")
        tracker.stop()
        db.close()
        print("¡Guardado con éxito!")

if __name__ == "__main__":
    main()