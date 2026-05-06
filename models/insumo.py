"""
models/insumo.py
Representa un insumo (materia prima) del inventario.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Insumo:
    """
    Modelo que representa un insumo / materia prima.

    Campos obligatorios al crear:
        nombre      — nombre descriptivo del insumo (ej. "Harina de trigo")
        unidad      — unidad de medida (ej. "kg", "L", "unidades")
        stock       — cantidad actual disponible
        stock_minimo— umbral por debajo del cual se lanza alerta
        precio_unit — precio de compra por unidad

    Campos gestionados automáticamente:
        id          — None hasta que el repositorio persiste el registro
        created_at  — fecha/hora de creación (ISO-8601)
        updated_at  — fecha/hora de última modificación (ISO-8601)
    """

    nombre: str
    unidad: str
    stock: float
    stock_minimo: float
    precio_unit: float

    id: int | None = field(default=None)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # ------------------------------------------------------------------
    # Propiedades de dominio
    # ------------------------------------------------------------------

    @property
    def bajo_stock(self) -> bool:
        """True cuando el stock actual está por debajo del mínimo."""
        return self.stock < self.stock_minimo

    @property
    def valor_total(self) -> float:
        """Valor monetario total del stock disponible."""
        return round(self.stock * self.precio_unit, 2)

    # ------------------------------------------------------------------
    # Conversión desde sqlite3.Row
    # ------------------------------------------------------------------

    @classmethod
    def from_row(cls, row) -> "Insumo":
        """
        Construye un Insumo a partir de un sqlite3.Row.
        Permite acceso por nombre de columna gracias a row_factory.
        """
        return cls(
            id=row["id"],
            nombre=row["nombre"],
            unidad=row["unidad"],
            stock=row["stock"],
            stock_minimo=row["stock_minimo"],
            precio_unit=row["precio_unit"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # ------------------------------------------------------------------
    # Representación
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        alerta = " ⚠ STOCK BAJO" if self.bajo_stock else ""
        return (
            f"Insumo(id={self.id}, nombre='{self.nombre}', "
            f"stock={self.stock} {self.unidad}{alerta})"
        )