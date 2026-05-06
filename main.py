# main.py

import customtkinter as ctk
from database.connection import DatabaseConnection
# --- NUEVA IMPORTACIÓN ---
from ui.inventory_view import InventoryView 

def main() -> None:
    # ------------------------------------------------------------------
    # 1. Inicializar la base de datos
    # ------------------------------------------------------------------
    db = DatabaseConnection.get_instance()
    db.connect()
    conn = db.get_connection() # Obtenemos la conexión real para los repositorios

    # ------------------------------------------------------------------
    # 2. Configuración global de CustomTkinter
    # ------------------------------------------------------------------
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # ------------------------------------------------------------------
    # 3. Ventana principal
    # ------------------------------------------------------------------
    app = ctk.CTk()
    app.title("Fast Food App - Medellín")
    app.geometry("1000x700") # Un poco más grande para la tabla
    app.minsize(800, 500)

    # Cerrar la conexión al salir
    app.protocol("WM_DELETE_WINDOW", lambda: (db.close(), app.destroy()))

    # ------------------------------------------------------------------
    # 4. Estructura de la Interfaz
    # ------------------------------------------------------------------
    
    # Título superior
    title_label = ctk.CTkLabel(
        app, 
        text="SISTEMA DE INVENTARIO", 
        font=ctk.CTkFont(size=24, weight="bold")
    )
    title_label.pack(pady=20)

    # Contenedor principal donde vivirán las vistas
    container = ctk.CTkFrame(app)
    container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    # --- INTEGRACIÓN DE LA FASE 2 ---
    # Instanciamos la vista de inventario y le pasamos la conexión
    inventory_page = InventoryView(container, conn)
    inventory_page.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # 5. Iniciar el loop principal
    # ------------------------------------------------------------------
    app.mainloop()

if __name__ == "__main__":
    main()