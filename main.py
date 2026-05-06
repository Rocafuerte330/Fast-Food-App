# main.py
import customtkinter as ctk
from database.connection import DatabaseConnection

# IMPORTACIONES DE LAS VISTAS (Asegúrate de tener estos archivos)
from ui.inventory_view import InventoryView 
from ui.products_view import ProductsView

def main() -> None:
    # ------------------------------------------------------------------
    # 1. Inicializar DB
    # ------------------------------------------------------------------
    db = DatabaseConnection.get_instance()
    db.connect()
    conn = db.get_connection()

    # ------------------------------------------------------------------
    # 2. Configuración Ventana
    # ------------------------------------------------------------------
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = ctk.CTk()
    app.title("Fast Food App - Medellín")
    app.geometry("1100x750")

    app.protocol("WM_DELETE_WINDOW", lambda: (db.close(), app.destroy()))

    # ------------------------------------------------------------------
    # 3. FUNCIONES DE NAVEGACIÓN (Deben estar antes de los botones)
    # ------------------------------------------------------------------
    def mostrar_inventario():
        products_page.pack_forget() # Esconde productos
        inventory_page.pack(fill="both", expand=True)

    def mostrar_productos():
        inventory_page.pack_forget() # Esconde inventario
        products_page.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # 4. LAYOUT: BARRA DE NAVEGACIÓN (SUPERIOR)
    # ------------------------------------------------------------------
    nav_frame = ctk.CTkFrame(app, height=60)
    nav_frame.pack(fill="x", padx=20, pady=10)

    btn_inv = ctk.CTkButton(nav_frame, text="📦 Inventario", command=mostrar_inventario)
    btn_inv.pack(side="left", padx=10, pady=10)

    btn_prod = ctk.CTkButton(nav_frame, text="🍔 Productos y Recetas", command=mostrar_productos)
    btn_prod.pack(side="left", padx=10, pady=10)

    # ------------------------------------------------------------------
    # 5. CONTENEDOR PRINCIPAL
    # ------------------------------------------------------------------
    container = ctk.CTkFrame(app)
    container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    # ------------------------------------------------------------------
    # 6. INSTANCIAR VISTAS (Aquí es donde se "pegan" los módulos)
    # ------------------------------------------------------------------
    inventory_page = InventoryView(container, conn)
    products_page = ProductsView(container, conn)

    # Mostrar inventario por defecto al arrancar
    inventory_page.pack(fill="both", expand=True)

    app.mainloop()

if __name__ == "__main__":
    main()