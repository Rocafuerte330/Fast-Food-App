"""
database/repositories/insumo_repository.py
CRUD de insumos — recibe db_connection por inyección de dependencias.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from models.insumo import Insumo


class InsumoRepository:
    """
    Maneja todas las operaciones de persistencia para la tabla `insumos`.

    Convenciones:
    - Recibe `connection` (sqlite3.Connection) en el constructor — no la crea.
    - row_factory = sqlite3.Row ya está activo en la conexión.
    - No usa print(): lanza excepciones para que la UI las capture.
    - Fechas en ISO-8601 via datetime.now().isoformat().
    """

    def __init__(self, connection) -> None:
        self._conn = connection

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def guardar(self, insumo: Insumo) -> Insumo:
        """
        Inserta un nuevo insumo.
        Retorna el mismo objeto con el id asignado por la DB.

        Raises:
            ValueError: si ya existe un insumo con el mismo nombre.
            RuntimeError: ante cualquier error de base de datos.
        """
        if self.buscar_por_nombre(insumo.nombre) is not None:
            raise ValueError(
                f"Ya existe un insumo con el nombre '{insumo.nombre}'."
            )

        sql = """
            INSERT INTO insumos (nombre, unidad, stock, stock_minimo, precio_unit,
                                 created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.now().isoformat()
        try:
            cursor = self._conn.execute(
                sql,
                (
                    insumo.nombre,
                    insumo.unidad,
                    insumo.stock,
                    insumo.stock_minimo,
                    insumo.precio_unit,
                    now,
                    now,
                ),
            )
            self._conn.commit()
            insumo.id = cursor.lastrowid
            insumo.created_at = now
            insumo.updated_at = now
            return insumo
        except Exception as exc:
            self._conn.rollback()
            raise RuntimeError(f"Error al guardar insumo: {exc}") from exc

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    def listar(self) -> list[Insumo]:
        """
        Retorna todos los insumos ordenados por nombre.
        """
        try:
            rows = self._conn.execute(
                "SELECT * FROM insumos ORDER BY nombre ASC"
            ).fetchall()
            return [Insumo.from_row(r) for r in rows]
        except Exception as exc:
            raise RuntimeError(f"Error al listar insumos: {exc}") from exc

    def buscar_por_id(self, insumo_id: int) -> Optional[Insumo]:
        """
        Retorna el insumo con ese id o None si no existe.
        """
        try:
            row = self._conn.execute(
                "SELECT * FROM insumos WHERE id = ?", (insumo_id,)
            ).fetchone()
            return Insumo.from_row(row) if row else None
        except Exception as exc:
            raise RuntimeError(f"Error al buscar insumo por id: {exc}") from exc

    def buscar_por_nombre(self, nombre: str) -> Optional[Insumo]:
        """
        Búsqueda exacta por nombre (case-insensitive gracias a COLLATE NOCASE).
        Retorna None si no existe.
        """
        try:
            row = self._conn.execute(
                "SELECT * FROM insumos WHERE nombre = ? COLLATE NOCASE",
                (nombre,),
            ).fetchone()
            return Insumo.from_row(row) if row else None
        except Exception as exc:
            raise RuntimeError(f"Error al buscar insumo por nombre: {exc}") from exc

    def listar_bajo_stock(self) -> list[Insumo]:
        """
        Retorna únicamente los insumos cuyo stock < stock_minimo.
        Útil para el panel de alertas.
        """
        try:
            rows = self._conn.execute(
                "SELECT * FROM insumos WHERE stock < stock_minimo ORDER BY nombre ASC"
            ).fetchall()
            return [Insumo.from_row(r) for r in rows]
        except Exception as exc:
            raise RuntimeError(f"Error al listar insumos con bajo stock: {exc}") from exc

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    def actualizar(self, insumo: Insumo) -> Insumo:
        """
        Actualiza todos los campos editables de un insumo existente.

        Raises:
            ValueError: si el insumo no tiene id o no existe en la DB.
            RuntimeError: ante error de base de datos.
        """
        if insumo.id is None:
            raise ValueError("El insumo no tiene id asignado; no se puede actualizar.")
        if self.buscar_por_id(insumo.id) is None:
            raise ValueError(f"No existe insumo con id={insumo.id}.")

        sql = """
            UPDATE insumos
            SET nombre = ?, unidad = ?, stock = ?, stock_minimo = ?,
                precio_unit = ?, updated_at = ?
            WHERE id = ?
        """
        now = datetime.now().isoformat()
        try:
            self._conn.execute(
                sql,
                (
                    insumo.nombre,
                    insumo.unidad,
                    insumo.stock,
                    insumo.stock_minimo,
                    insumo.precio_unit,
                    now,
                    insumo.id,
                ),
            )
            self._conn.commit()
            insumo.updated_at = now
            return insumo
        except Exception as exc:
            self._conn.rollback()
            raise RuntimeError(f"Error al actualizar insumo: {exc}") from exc

    def actualizar_stock(self, insumo_id: int, cantidad: float) -> Insumo:
        """
        Ajusta el stock de un insumo en `cantidad` unidades (positivo = entrada,
        negativo = salida). Verifica que el resultado no quede negativo.

        Raises:
            ValueError: stock insuficiente o insumo inexistente.
            RuntimeError: error de base de datos.
        """
        insumo = self.buscar_por_id(insumo_id)
        if insumo is None:
            raise ValueError(f"No existe insumo con id={insumo_id}.")

        nuevo_stock = insumo.stock + cantidad
        if nuevo_stock < 0:
            raise ValueError(
                f"Stock insuficiente para '{insumo.nombre}'. "
                f"Disponible: {insumo.stock} {insumo.unidad}, "
                f"solicitado: {abs(cantidad)} {insumo.unidad}."
            )

        now = datetime.now().isoformat()
        try:
            self._conn.execute(
                "UPDATE insumos SET stock = ?, updated_at = ? WHERE id = ?",
                (nuevo_stock, now, insumo_id),
            )
            self._conn.commit()
            insumo.stock = nuevo_stock
            insumo.updated_at = now
            return insumo
        except Exception as exc:
            self._conn.rollback()
            raise RuntimeError(f"Error al actualizar stock: {exc}") from exc

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def eliminar(self, insumo_id: int) -> None:
        """
        Elimina un insumo por id.

        Raises:
            ValueError: si el insumo no existe.
            RuntimeError: si hay restricciones de FK o error de DB.
        """
        if self.buscar_por_id(insumo_id) is None:
            raise ValueError(f"No existe insumo con id={insumo_id}.")

        try:
            self._conn.execute(
                "DELETE FROM insumos WHERE id = ?", (insumo_id,)
            )
            self._conn.commit()
        except Exception as exc:
            self._conn.rollback()
            raise RuntimeError(
                f"Error al eliminar insumo (¿tiene recetas asociadas?): {exc}"
            ) from exc
