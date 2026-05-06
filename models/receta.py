"""
models/receta.py
Representa una línea de receta: qué insumo y cuánto requiere un producto.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Receta:
    """
    Vincula un Producto con un Insumo indicando la cantidad necesaria
    para producir una unidad del producto.

    La combinación (producto_id, insumo_id) es única en la DB.

    Campos opcionales enriquecidos (se cargan con JOINs en el repositorio):
        nombre_insumo  — para mostrar en la UI sin hacer otra consulta
        unidad_insumo  — unidad de medida del insumo
        stock_insumo   — stock actual (útil para validar viabilidad)
    """

    producto_id: int
    insumo_id: int
    cantidad_requerida: float

    id: int | None = field(default=None)

    # Campos enriquecidos opcionales (JOIN)
    nombre_insumo: str | None = field(default=None)
    unidad_insumo: str | None = field(default=None)
    stock_insumo: float | None = field(default=None)

    # ------------------------------------------------------------------
    # Propiedades de dominio
    # ------------------------------------------------------------------

    @property
    def insumo_disponible(self) -> bool | None:
        """
        None si no se cargó el stock.
        True si hay stock suficiente para al menos 1 unidad del producto.
        """
        if self.stock_insumo is None:
            return None
        return self.stock_insumo >= self.cantidad_requerida

    # ------------------------------------------------------------------
    # Conversión desde sqlite3.Row
    # ------------------------------------------------------------------

    @classmethod
    def from_row(cls, row) -> "Receta":
        """Soporta tanto filas simples como filas con JOIN."""
        keys = row.keys()
        return cls(
            id=row["id"],
            producto_id=row["producto_id"],
            insumo_id=row["insumo_id"],
            cantidad_requerida=row["cantidad_requerida"],
            nombre_insumo=row["nombre_insumo"] if "nombre_insumo" in keys else None,
            unidad_insumo=row["unidad_insumo"] if "unidad_insumo" in keys else None,
            stock_insumo=row["stock_insumo"]   if "stock_insumo"  in keys else None,
        )

    def __str__(self) -> str:
        insumo = self.nombre_insumo or f"insumo_id={self.insumo_id}"
        return (
            f"Receta(producto_id={self.producto_id}, "
            f"insumo='{insumo}', cantidad={self.cantidad_requerida})"
        )
