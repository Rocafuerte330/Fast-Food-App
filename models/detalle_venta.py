"""
models/detalle_venta.py
Modelo de datos para un ítem dentro de una venta (línea de detalle).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DetalleVenta:
    """
    Representa una línea de detalle de venta en la tabla `detalle_ventas`.

    Atributos enriquecidos opcionales (presentes solo si se hizo JOIN con `productos`):
      - nombre_producto: nombre del producto
      - categoria:       categoría del producto
    """

    id: Optional[int]
    venta_id: int
    producto_id: int
    cantidad: int
    precio_unitario: float

    # Campos enriquecidos (JOIN con productos) — None si no se realizó JOIN
    nombre_producto: Optional[str] = None
    categoria: Optional[str] = None

    # ------------------------------------------------------------------ #
    # Propiedades                                                          #
    # ------------------------------------------------------------------ #

    @property
    def subtotal(self) -> float:
        """Subtotal de esta línea: cantidad × precio_unitario."""
        return self.cantidad * self.precio_unitario

    @property
    def subtotal_fmt(self) -> str:
        """Subtotal formateado con 2 decimales."""
        return f"${self.subtotal:,.2f}"

    @property
    def precio_unitario_fmt(self) -> str:
        return f"${self.precio_unitario:,.2f}"

    # ------------------------------------------------------------------ #
    # Constructor desde sqlite3.Row                                       #
    # ------------------------------------------------------------------ #

    @classmethod
    def from_row(cls, row) -> "DetalleVenta":
        """
        Crea una instancia a partir de un sqlite3.Row.
        Detecta automáticamente si están disponibles los campos enriquecidos del JOIN.
        """
        keys = row.keys()
        return cls(
            id=row["id"],
            venta_id=row["venta_id"],
            producto_id=row["producto_id"],
            cantidad=row["cantidad"],
            precio_unitario=row["precio_unitario"],
            nombre_producto=row["nombre_producto"] if "nombre_producto" in keys else None,
            categoria=row["categoria"] if "categoria" in keys else None,
        )
