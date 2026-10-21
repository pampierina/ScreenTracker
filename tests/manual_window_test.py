"""Test manual: imprime la ventana activa cada 2 segundos."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from platform_utils import get_provider

def main() -> None:
    print("Iniciando prueba de lectura de ventanas...")
    try:
        provider = get_provider()
    except Exception as e:
        print(f"Error al iniciar el proveedor: {e}")
        return

    ok, msg = provider.is_supported()
    print(f"Estado: {msg}\n")
    
    if not ok and "Wayland" in msg:
        print("⚠️ Estás en Wayland. El test intentará usar xdotool.")
        print("Si no funciona, cierra sesión y entra con 'Ubuntu on Xorg'.\n")

    try:
        while True:
            window = provider.get_active_window()
            idle_time = provider.get_idle_seconds()
            
            if window:
                print(f"[{time.strftime('%H:%M:%S')}] App: {window.app_name:<15} | PID: {window.pid} | Idle: {idle_time}s | Título: {window.window_title}")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] No se detecta ventana activa | Idle: {idle_time}s")
                
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nPrueba detenida por el usuario.")

if __name__ == "__main__":
    main()