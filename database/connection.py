# database/connection.py

import sqlite3
import os
from database.schema import SQL_SCHEMA


# Ruta al archivo .db relativa a la raíz del proyecto.
# __file__ apunta a database/connection.py,
# así que subimos un nivel con dirname(dirname(...)).
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_BASE_DIR, "fast_food.db")


class DatabaseConnection:
    """
    Gestiona la conexión SQLite como un singleton simple.

    Uso:
        db = DatabaseConnection.get_instance()
        conn = db.get_connection()
        cursor = conn.cursor()
    """

    _instance: "DatabaseConnection | None" = None

    def __init__(self) -> None:
        self._connection: sqlite3.Connection | None = None

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------
    @classmethod
    def get_instance(cls) -> "DatabaseConnection":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Ciclo de vida de la conexión
    # ------------------------------------------------------------------
    def connect(self) -> None:
        """
        Abre la conexión. Si el archivo .db no existe, SQLite lo crea
        y luego ejecutamos el schema para inicializar las tablas.
        """
        db_exists = os.path.exists(DB_PATH)

        self._connection = sqlite3.connect(DB_PATH)

        # Devuelve filas como diccionarios (acceso por nombre de columna)
        self._connection.row_factory = sqlite3.Row

        # Activa las foreign keys (SQLite las ignora por defecto)
        self._connection.execute("PRAGMA foreign_keys = ON;")

        if not db_exists:
            print(f"[DB] Archivo nuevo detectado. Inicializando schema en: {DB_PATH}")
            self._initialize_schema()
        else:
            print(f"[DB] Conectado a base de datos existente: {DB_PATH}")

    def _initialize_schema(self) -> None:
        """Ejecuta el SQL_SCHEMA completo usando executescript."""
        try:
            self._connection.executescript(SQL_SCHEMA)
            self._connection.commit()
            print("[DB] Schema creado correctamente.")
        except sqlite3.Error as e:
            print(f"[DB] Error al crear el schema: {e}")
            raise

    def get_connection(self) -> sqlite3.Connection:
        """
        Devuelve la conexión activa.
        Lanza RuntimeError si se llama antes de connect().
        """
        if self._connection is None:
            raise RuntimeError(
                "La base de datos no está inicializada. "
                "Llama a DatabaseConnection.get_instance().connect() primero."
            )
        return self._connection

    def close(self) -> None:
        """Cierra la conexión limpiamente al salir de la app."""
        if self._connection:
            self._connection.close()
            self._connection = None
            print("[DB] Conexión cerrada.")