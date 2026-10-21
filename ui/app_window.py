"""Ventana principal de la aplicación ScreenTracker."""
import customtkinter as ctk
from datetime import datetime
from storage.database import Database
from tracker.session_manager import Tracker

class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración básica de la ventana
        self.title("ScreenTracker")
        self.geometry("450x600")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Inicializar Base de datos y Tracker
        self.db = Database()
        self.tracker = Tracker(self.db)
        
        # Iniciar el tracker en segundo plano automáticamente al abrir
        self.tracker.start()

        self._setup_ui()
        self._update_ui() # Iniciar el bucle de actualización visual

        # Detectar cuando se cierra la ventana para guardar datos y salir limpiamente
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_ui(self):
        # --- Título ---
        self.title_label = ctk.CTkLabel(
            self, text="ScreenTracker", 
            font=("Arial", 24, "bold")
        )
        self.title_label.pack(pady=(20, 10))

        # --- Estado actual ---
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.pack(pady=10, padx=20, fill="x")

        self.current_app_label = ctk.CTkLabel(
            self.status_frame, text="App actual: Ninguna", 
            font=("Arial", 16)
        )
        self.current_app_label.pack(pady=(10, 5))

        self.current_time_label = ctk.CTkLabel(
            self.status_frame, text="Tiempo en sesión: 0s", 
            font=("Arial", 14), text_color="gray"
        )
        self.current_time_label.pack(pady=(0, 10))

        # --- Botón ON/OFF ---
        self.toggle_btn = ctk.CTkButton(
            self, text="Detener Tracking", 
            command=self._toggle_tracking,
            font=("Arial", 16, "bold"),
            fg_color="#c0392b", hover_color="#e74c3c"
        )
        self.toggle_btn.pack(pady=20, padx=20, fill="x")
        
        # Comprobar estado inicial del botón
        self._update_button_state()

        # --- Resumen del día ---
        self.summary_label = ctk.CTkLabel(
            self, text="Resumen de hoy", 
            font=("Arial", 18, "bold")
        )
        self.summary_label.pack(pady=(10, 5))

        self.summary_textbox = ctk.CTkTextbox(
            self, width=380, height=200, 
            font=("Arial", 14)
        )
        self.summary_textbox.pack(pady=10, padx=20)
        self.summary_textbox.configure(state="disabled") # Solo lectura

    def _toggle_tracking(self):
        """Activa o desactiva el tracking manualmente."""
        current_state = self.db.get_tracking_enabled()
        new_state = not current_state
        self.db.set_tracking_enabled(new_state)
        self._update_button_state()

    def _update_button_state(self):
        """Cambia el texto y color del botón según el estado en la BD."""
        if self.db.get_tracking_enabled():
            self.toggle_btn.configure(text="Detener Tracking", fg_color="#c0392b", hover_color="#e74c3c")
        else:
            self.toggle_btn.configure(text="Iniciar Tracking", fg_color="#27ae60", hover_color="#2ecc71")

    def _update_ui(self):
        """Se ejecuta cada segundo para actualizar la ventana."""
        # 1. Actualizar estado actual
        app, secs = self.tracker.get_current_status()
        
        if app == "Ninguna":
            self.current_app_label.configure(text="App actual: En pausa / Inactivo")
            self.current_time_label.configure(text="Tiempo en sesión: 0s")
        else:
            self.current_app_label.configure(text=f"App actual: {app}")
            self.current_time_label.configure(text=f"Tiempo en sesión: {secs}s")

        # 2. Actualizar resumen del día
        self._update_summary()

        # 3. Volver a llamar a esta función en 1 segundo (1000 ms)
        self.after(1000, self._update_ui)

    def _update_summary(self):
        """Lee la base de datos y actualiza el cuadro de texto con los totales de hoy."""
        hoy = datetime.now().date()
        resumen = self.db.get_daily_summary(hoy)
        
        # Guardamos la posición actual del scroll
        self.summary_textbox.configure(state="normal")
        self.summary_textbox.delete("1.0", "end")
        
        if not resumen:
            self.summary_textbox.insert("1.0", "Aún no hay datos registrados hoy.")
        else:
            texto = ""
            for fila in resumen:
                mins = fila["total_seconds"] // 60
                segs = fila["total_seconds"] % 60
                # Formateamos para que quede alineado
                texto += f"• {fila['app_name']:<12} {mins:>3} min {segs:>2} s\n"
            
            self.summary_textbox.insert("1.0", texto)
            
        self.summary_textbox.configure(state="disabled")

    def _on_closing(self):
        """Se ejecuta al cerrar la ventana."""
        print("Cerrando aplicación...")
        self.tracker.stop()
        self.db.close()
        self.destroy()