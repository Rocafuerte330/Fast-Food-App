# main.py

import customtkinter as ctk
from database.connection import DatabaseConnection


def test_db_connection() -> None:
    """
    Callback del botón 'Test DB'.
    Ejecuta una query liviana para verificar que la conexión
    y las tablas existen correctamente.
    """
    try:
        db = DatabaseConnection.get_instance()
        conn = db.get_connection()
        cursor = conn.cursor()

        # Leer la lista de tablas es una prueba real sin side-effects
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tablas = [row["name"] for row in cursor.fetchall()]

        print("✅ Conexión exitosa.")
        print(f"   Tablas encontradas ({len(tablas)}): {', '.join(tablas)}")

    except Exception as e:
        print(f"❌ Error en la conexión: {e}")


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Inicializar la base de datos ANTES de levantar la UI
    # ------------------------------------------------------------------
    db = DatabaseConnection.get_instance()
    db.connect()

    # ------------------------------------------------------------------
    # 2. Configuración global de CustomTkinter
    # ------------------------------------------------------------------
    ctk.set_appearance_mode("dark")          # "dark" | "light" | "system"
    ctk.set_default_color_theme("blue")

    # ------------------------------------------------------------------
    # 3. Ventana principal
    # ------------------------------------------------------------------
    app = ctk.CTk()
    app.title("Fast Food App - Medellín")
    app.geometry("900x600")
    app.minsize(700, 450)

    # Cerrar la conexión a SQLite cuando el usuario cierra la ventana
    app.protocol("WM_DELETE_WINDOW", lambda: (db.close(), app.destroy()))

    # ------------------------------------------------------------------
    # 4. Layout de prueba (se reemplazará con las vistas reales)
    # ------------------------------------------------------------------
    frame = ctk.CTkFrame(app)
    frame.pack(expand=True)

    label = ctk.CTkLabel(
        frame,
        text="Fast Food App",
        font=ctk.CTkFont(size=28, weight="bold"),
    )
    label.pack(pady=(40, 8))

    subtitle = ctk.CTkLabel(
        frame,
        text="Medellín 🇨🇴",
        font=ctk.CTkFont(size=14),
        text_color="gray",
    )
    subtitle.pack(pady=(0, 32))

    btn_test = ctk.CTkButton(
        frame,
        text="Test DB",
        width=160,
        command=test_db_connection,
    )
    btn_test.pack()

    # ------------------------------------------------------------------
    # 5. Iniciar el loop principal
    # ------------------------------------------------------------------
    app.mainloop()


if __name__ == "__main__":
    main()