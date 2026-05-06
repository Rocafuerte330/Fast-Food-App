"""
database/repositories/producto_repository.py
CRUD de productos — recibe db_connection por inyección de dependencias.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from models.producto import Producto


class ProductoRepository:
    """
    Maneja todas las operaciones de persistencia para la tabla `productos`.

    Convenciones (igual que InsumoRepository):
    - Recibe `connection` en el constructor — no la crea.
    - No usa print(): lanza ValueError (lógica) o RuntimeError (DB).
    - Fechas ISO-8601 via datetime.now().isoformat().
    """

    def __init__(self, connection) -> None:
        self._conn = connection

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def guardar(self, producto: Producto) -> Producto:
        """
        Inserta un nuevo producto.
        Retorna el objeto con id asignado.

        Raises:
            ValueError: nombre duplicado.
            RuntimeError: error de DB.
        """
        if self.buscar_por_nombre(producto.nombre) is not None:
            raise ValueError(
                f"Ya existe un producto con el nombre '{producto.nombre}'."
            )

        sql = """
            INSERT INTO productos (nombre, categoria, precio_venta, activo, created_at)
            VALUES (?, ?, ?, ?, ?)
        """
        now = datetime.now().isoformat()
        try:
            cursor = self._conn.execute(
                sql,
                (
                    producto.nombre,
                    producto.categoria,
                    producto.precio_venta,
                    int(producto.activo),
                    now,
                ),
            )
            self._conn.commit()
            producto.id = cursor.lastrowid
            producto.created_at = now
            return producto
        except Exception as exc:
            self._conn.rollback()
            raise RuntimeError(f"Error al guardar producto: {exc}") from exc

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    def listar(self, solo_activos: bool = False) -> list[Producto]:
        """
        Retorna todos los productos ordenados por categoria y nombre.
        Si solo_activos=True, excluye los productos con activo=0.
        """
        where = "WHERE activo = 1" if solo_activos else ""
        try:
            rows = self._conn.execute(
                f"SELECT * FROM productos {where} ORDER BY categoria ASC, nombre ASC"
            ).fetchall()
            return [Producto.from_row(r) for r in rows]
        except Exception as exc:
            raise RuntimeError(f"Error al listar productos: {exc}") from exc

    def listar_por_categoria(self, categoria: str) -> list[Producto]:
        """Retorna productos activos de una categoría específica."""
        try:
            rows = self._conn.execute(
                "SELECT * FROM productos WHERE categoria = ? AND activo = 1 ORDER BY nombre ASC",
                (categoria,),
            ).fetchall()
            return [Producto.from_row(r) for r in rows]
        except Exception as exc:
            raise RuntimeError(f"Error al listar productos por categoría: {exc}") from exc

    def listar_categorias(self) -> list[str]:
        """Retorna las categorías únicas existentes, ordenadas."""
        try:
            rows = self._conn.execute(
                "SELECT DISTINCT categoria FROM productos ORDER BY categoria ASC"
            ).fetchall()
            return [r["categoria"] for r in rows]
        except Exception as exc:
            raise RuntimeError(f"Error al listar categorías: {exc}") from exc

    def buscar_por_id(self, producto_id: int) -> Optional[Producto]:
        try:
            row = self._conn.execute(
                "SELECT * FROM productos WHERE id = ?", (producto_id,)
            ).fetchone()
            return Producto.from_row(row) if row else None
        except Exception as exc:
            raise RuntimeError(f"Error al buscar producto por id: {exc}") from exc

    def buscar_por_nombre(self, nombre: str) -> Optional[Producto]:
        try:
            row = self._conn.execute(
                "SELECT * FROM productos WHERE nombre = ? COLLATE NOCASE", (nombre,)
            ).fetchone()
            return Producto.from_row(row) if row else None
        except Exception as exc:
            raise RuntimeError(f"Error al buscar producto por nombre: {exc}") from exc

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    def actualizar(self, producto: Producto) -> Producto:
        """
        Actualiza nombre, categoría, precio y estado activo.

        Raises:
            ValueError: sin id o inexistente.
            RuntimeError: error de DB.
        """
        if producto.id is None:
            raise ValueError("El producto no tiene id asignado.")
        if self.buscar_por_id(producto.id) is None:
            raise ValueError(f"No existe producto con id={producto.id}.")

        sql = """
            UPDATE productos
            SET nombre = ?, categoria = ?, precio_venta = ?, activo = ?
            WHERE id = ?
        """
        try:
            self._conn.execute(
                sql,
                (
                    producto.nombre,
                    producto.categoria,
                    producto.precio_venta,
                    int(producto.activo),
                    producto.id,
                ),
            )
            self._conn.commit()
            return producto
        except Exception as exc:
            self._conn.rollback()
            raise RuntimeError(f"Error al actualizar producto: {exc}") from exc

    def cambiar_estado(self, producto_id: int, activo: bool) -> None:
        """Activa o desactiva un producto (soft delete)."""
        if self.buscar_por_id(producto_id) is None:
            raise ValueError(f"No existe producto con id={producto_id}.")
        try:
            self._conn.execute(
                "UPDATE productos SET activo = ? WHERE id = ?",
                (int(activo), producto_id),
            )
            self._conn.commit()
        except Exception as exc:
            self._conn.rollback()
            raise RuntimeError(f"Error al cambiar estado del producto: {exc}") from exc

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def eliminar(self, producto_id: int) -> None:
        """
        Elimina un producto permanentemente.
        Fallará si tiene ventas asociadas (FK RESTRICT en detalle_ventas).
        Las recetas se eliminan en cascada (FK CASCADE en recetas).

        Raises:
            ValueError: producto inexistente.
            RuntimeError: tiene ventas asociadas u otro error de DB.
        """
        if self.buscar_por_id(producto_id) is None:
            raise ValueError(f"No existe producto con id={producto_id}.")
        try:
            self._conn.execute(
                "DELETE FROM productos WHERE id = ?", (producto_id,)
            )
            self._conn.commit()
        except Exception as exc:
            self._conn.rollback()
            raise RuntimeError(
                f"Error al eliminar producto (¿tiene ventas registradas?): {exc}"
            ) from exc
