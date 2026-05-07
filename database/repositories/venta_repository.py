"""
database/repositories/venta_repository.py
CRUD y consultas para las tablas `ventas` y `detalle_ventas`.

Convenciones:
  - Recibe db_connection por inyección (no la crea internamente).
  - Usa row_factory = sqlite3.Row → acceso a columnas por nombre.
  - Fechas en ISO-8601.
  - No hace print(); lanza excepciones que la capa superior captura.
"""

import sqlite3
from typing import Optional
from models.venta import Venta
from models.detalle_venta import DetalleVenta


class VentaRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection

    # ================================================================== #
    # VENTAS                                                              #
    # ================================================================== #

    def crear(
        self,
        total: float,
        metodo_pago: str = "efectivo",
        descontar_insumos: bool = True,
    ) -> int:
        """
        Inserta una nueva venta y devuelve su id.
        La fecha se asigna automáticamente por SQLite (datetime('now')).
        """
        cur = self._conn.execute(
            """
            INSERT INTO ventas (total, metodo_pago, descontar_insumos)
            VALUES (?, ?, ?)
            """,
            (total, metodo_pago, int(descontar_insumos)),
        )
        self._conn.commit()
        return cur.lastrowid

    def obtener(self, venta_id: int) -> Optional[Venta]:
        """Devuelve la venta por id, o None si no existe."""
        row = self._conn.execute(
            "SELECT * FROM ventas WHERE id = ?", (venta_id,)
        ).fetchone()
        return Venta.from_row(row) if row else None

    def listar(self, limit: int = 100, offset: int = 0) -> list[Venta]:
        """Lista las ventas más recientes (desc), con paginación opcional."""
        rows = self._conn.execute(
            "SELECT * FROM ventas ORDER BY fecha DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [Venta.from_row(r) for r in rows]

    def listar_por_rango(self, fecha_inicio: str, fecha_fin: str) -> list[Venta]:
        """
        Lista ventas en un rango de fechas ISO-8601 (inclusive en ambos extremos).
        Aprovecha el índice idx_ventas_fecha.
        """
        rows = self._conn.execute(
            """
            SELECT * FROM ventas
            WHERE fecha BETWEEN ? AND ?
            ORDER BY fecha DESC
            """,
            (fecha_inicio, fecha_fin),
        ).fetchall()
        return [Venta.from_row(r) for r in rows]

    def eliminar(self, venta_id: int) -> bool:
        """
        Elimina la venta. Los detalles se borran en cascada (ON DELETE CASCADE).
        Devuelve True si se eliminó al menos 1 fila.
        """
        cur = self._conn.execute(
            "DELETE FROM ventas WHERE id = ?", (venta_id,)
        )
        self._conn.commit()
        return cur.rowcount > 0

    def total_del_dia(self, fecha_iso: str) -> float:
        """
        Suma de `total` de todas las ventas cuya fecha comienza con `fecha_iso`
        (formato 'YYYY-MM-DD').  Útil para el resumen diario.
        """
        row = self._conn.execute(
            "SELECT COALESCE(SUM(total), 0) AS suma FROM ventas WHERE fecha LIKE ?",
            (f"{fecha_iso}%",),
        ).fetchone()
        return float(row["suma"])

    # ================================================================== #
    # DETALLE_VENTAS                                                      #
    # ================================================================== #

    def agregar_detalle(
        self,
        venta_id: int,
        producto_id: int,
        cantidad: int,
        precio_unitario: float,
    ) -> int:
        """Inserta una línea de detalle y devuelve su id."""
        cur = self._conn.execute(
            """
            INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario)
            VALUES (?, ?, ?, ?)
            """,
            (venta_id, producto_id, cantidad, precio_unitario),
        )
        self._conn.commit()
        return cur.lastrowid

    def listar_detalles(self, venta_id: int) -> list[DetalleVenta]:
        """
        Lista los detalles de una venta con JOIN a `productos`
        para obtener nombre_producto y categoria.
        Aprovecha el índice idx_detalle_venta_id.
        """
        rows = self._conn.execute(
            """
            SELECT
                dv.id,
                dv.venta_id,
                dv.producto_id,
                dv.cantidad,
                dv.precio_unitario,
                p.nombre  AS nombre_producto,
                p.categoria
            FROM detalle_ventas dv
            JOIN productos p ON p.id = dv.producto_id
            WHERE dv.venta_id = ?
            ORDER BY dv.id
            """,
            (venta_id,),
        ).fetchall()
        return [DetalleVenta.from_row(r) for r in rows]

    def productos_mas_vendidos(self, limit: int = 10) -> list[dict]:
        """
        Devuelve los `limit` productos con mayor cantidad total vendida.
        Cada elemento: {'producto_id', 'nombre', 'total_vendido', 'ingresos'}.
        """
        rows = self._conn.execute(
            """
            SELECT
                p.id   AS producto_id,
                p.nombre,
                SUM(dv.cantidad)                   AS total_vendido,
                SUM(dv.cantidad * dv.precio_unitario) AS ingresos
            FROM detalle_ventas dv
            JOIN productos p ON p.id = dv.producto_id
            GROUP BY p.id
            ORDER BY total_vendido DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
