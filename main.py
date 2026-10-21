"""Punto de entrada principal de ScreenTracker."""
import sys
from pathlib import Path

# Añadimos la carpeta raíz al path para evitar errores de importación
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ui.app_window import AppWindow

def main():
    app = AppWindow()
    app.mainloop()

if __name__ == "__main__":
    main()