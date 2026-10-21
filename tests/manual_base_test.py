"""Test manual para verificar la detección de inactividad (Idle)."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from platform_utils import get_provider

def main() -> None:
    print("--- Test de Inactividad (Idle) ---")
    print("Mueve el ratón o escribe para reiniciar el contador.")
    print("Deja de tocar el teclado/ratón para ver cómo sube.")
    print("Presiona Ctrl+C para salir.\n")

    try:
        provider = get_provider()
    except Exception as e:
        print(f"Error: {e}")
        return

    try:
        while True:
            segundos = provider.get_idle_seconds()
            
            # Formateamos el tiempo para que sea legible
            minutos = segundos // 60
            segs_restantes = segundos % 60
            
            print(f"Tiempo inactivo: {minutos}m {segs_restantes}s (Total: {segundos}s)")
            time.sleep(1) # Actualizamos cada segundo para ver el cambio rápido
            
    except KeyboardInterrupt:
        print("\nTest detenido.")

if __name__ == "__main__":
    main()