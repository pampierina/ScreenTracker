"""Test para comprobar que la base de datos guarda y lee datos."""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from storage.database import Database

def main():
    print("--- Iniciando test de Base de Datos ---")
    db = Database()
    print(f"Base de datos creada en:\n{db.db_path}\n")

    # 1. Probar estado del botón ON/OFF
    print(f"Estado inicial del tracking: {'Encendido' if db.get_tracking_enabled() else 'Apagado'}")
    db.set_tracking_enabled(False)
    print(f"Apagando tracking... Ahora está: {'Encendido' if db.get_tracking_enabled() else 'Apagado'}")
    db.set_tracking_enabled(True) # Lo volvemos a encender

    # 2. Insertar datos falsos (simulando que usaste Brave y VS Code)
    print("\nInsertando sesiones de prueba (Brave y VS Code)...")
    ahora = datetime.now()
    
    db.insert_session(
        app_name="Brave", 
        process_name="brave", 
        pid=8940, 
        start_time=ahora, 
        duration_seconds=120 # 2 minutos
    )
    db.insert_session(
        app_name="Code", 
        process_name="code", 
        pid=3825, 
        start_time=ahora, 
        duration_seconds=300 # 5 minutos
    )

    # 3. Leer el resumen del día de hoy
    print("\n--- Resumen de hoy ---")
    resumen = db.get_daily_summary(ahora.date())
    
    if not resumen:
        print("No hay datos.")
    
    for fila in resumen:
        mins = fila["total_seconds"] // 60
        segs = fila["total_seconds"] % 60
        print(f"{fila['app_name']:<10}: {mins} min {segs} seg")

    print("\n¡Base de datos funcionando correctamente!")
    db.close()

if __name__ == "__main__":
    main()