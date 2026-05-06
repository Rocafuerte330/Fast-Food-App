"""
database/repositories/receta_repository.py
CRUD de recetas — recibe db_connection por inyección de dependencias.
"""

from __future__ import annotations
from typing import Optional

from models.receta import Receta


class RecetaRepository:
    """
    Maneja todas las operaciones de persistencia para la tabla `recetas`.

    La tabla recetas es la tabla pivote entre productos e insumos.
    Los métodos más importantes son los de lectura enriquecida (con JOIN)
    que la UI y los servicios necesitan para operar.
    """

    def __init__(self, connection) -> None:
        self._conn = connection

    # ------------------------------------------------------------------
    # SQL de JOIN reutilizable
    # ------------------------------------------------------------------

    _SQL_CON_INSUMO = """
        SELECT
            r.id,
            r.producto_id,
            r.insumo_id,
            r.cantidad_requerida,
            i.nombre  AS nombre_insumo,
            i.unidad  AS unidad_insumo,
            i.stock   AS stock_insumo
        FROM recetas r
        JOIN insumos i ON i.id = r.insumo_id
    """

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def guardar(self, receta: Receta) -> Receta:
        """
        Inserta una línea de receta.
        La combinación (producto_id, insumo_id) es UNIQUE en la DB.

        Raises:
            ValueError: combinación duplicada o cantidad <= 0.
            RuntimeError: error de DB.
        """
        if receta.cantidad_requerida <= 0:
            raise ValueError("La cantidad requerida debe ser mayor que cero.")

        if self.buscar(receta.producto_id, receta.insumo_id) is not None:
            raise ValueError(
                f"Ya existe una línea de receta para "
                f"producto_id={receta.producto_id} e insumo_id={receta.insumo_id}."
            )

        sql = """
            INSERT INTO recetas (producto_id, insumo_id, cantidad_requerida)
            VALUES (?, ?, ?)
        """
        try:
            cursor = self._conn.execute(
                sql,
                (receta.producto_id, receta.insumo_id, receta.cantidad_requerida),
            )
            self._conn.commit()
            receta.id = cursor.lastrowid
            return receta
        except Exception as exc:
            self._conn.rollback()
            raise RuntimeError(f"Error al guardar receta: {exc}") from exc

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    def listar_por_producto(self, producto_id: int) -> list[Receta]:
        """
        Retorna todas las líneas de receta de un producto,
        enriquecidas con nombre, unidad y stock del insumo.
        """
        try:
            rows = self._conn.execute(
                self._SQL_CON_INSUMO + " WHERE r.producto_id = ? ORDER BY i.nombre ASC",
                (producto_id,),
            ).fetchall()
            return [Receta.from_row(r) for r in rows]
        except Exception as exc:
            raise RuntimeError(f"Error al listar receta del producto: {exc}") from exc

    def buscar(self, producto_id: int, insumo_id: int) -> Optional[Receta]:
        """Busca una línea específica por la combinación única."""
        try:
            row = self._conn.execute(
                self._SQL_CON_INSUMO
                + " WHERE r.producto_id = ? AND r.insumo_id = ?",
                (producto_id, insumo_id),
            ).fetchone()
            return Receta.from_row(row) if row else None
        except Exception as exc:
            raise RuntimeError(f"Error al buscar línea de receta: {exc}") from exc

    def buscar_por_id(self, receta_id: int) -> Optional[Receta]:
        try:
            row = self._conn.execute(
                self._SQL_CON_INSUMO + " WHERE r.id = ?", (receta_id,)
            ).fetchone()
            return Receta.from_row(row) if row else None
        except Exception as exc:
            raise RuntimeError(f"Error al buscar receta por id: {exc}") from exc

    def verificar_stock_para_producto(
        self, producto_id: int, cantidad_unidades: int = 1
    ) -> tuple[bool, list[Receta]]:
        """
        Verifica si hay stock suficiente para producir `cantidad_unidades`
        del producto.

        Retorna:
            (True, [])               — stock OK para todas las líneas
            (False, [líneas_faltantes]) — lista de recetas con stock insuficiente
        """
        recetas = self.listar_por_producto(producto_id)
        faltantes = [
            r for r in recetas
            if r.stock_insumo is not None
            and r.stock_insumo < r.cantidad_requerida * cantidad_unidades
        ]
        return (len(faltantes) == 0, faltantes)

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    def actualizar_cantidad(self, receta_id: int, nueva_cantidad: float) -> Receta:
        """
        Actualiza solo la cantidad requerida de una línea de receta.

        Raises:
            ValueError: receta inexistente o cantidad <= 0.
            RuntimeError: error de DB.
        """
        if nueva_cantidad <= 0:
            raise ValueError("La cantidad requerida debe ser mayor que cero.")

        receta = self.buscar_por_id(receta_id)
        if receta is None:
            raise ValueError(f"No existe receta con id={receta_id}.")

        try:
            self._conn.execute(
                "UPDATE recetas SET cantidad_requerida = ? WHERE id = ?",
                (nueva_cantidad, receta_id),
            )
            self._conn.commit()
            receta.cantidad_requerida = nueva_cantidad
            return receta
        except Exception as exc:
            self._conn.rollback()
            raise RuntimeError(f"Error al actualizar cantidad de receta: {exc}") from exc

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def eliminar(self, receta_id: int) -> None:
        """Elimina una línea de receta por id."""
        if self.buscar_por_id(receta_id) is None:
            raise ValueError(f"No existe receta con id={receta_id}.")
        try:
            self._conn.execute("DELETE FROM recetas WHERE id = ?", (receta_id,))
            self._conn.commit()
        except Exception as exc:
            self._conn.rollback()
            raise RuntimeError(f"Error al eliminar línea de receta: {exc}") from exc

    def eliminar_por_producto(self, producto_id: int) -> int:
        """
        Elimina TODAS las líneas de receta de un producto.
        Útil antes de reemplazar la receta completa.
        Retorna el número de filas eliminadas.
        """
        try:
            cursor = self._conn.execute(
                "DELETE FROM recetas WHERE producto_id = ?", (producto_id,)
            )
            self._conn.commit()
            return cursor.rowcount
        except Exception as exc:
            self._conn.rollback()
            raise RuntimeError(f"Error al eliminar recetas del producto: {exc}") from exc
