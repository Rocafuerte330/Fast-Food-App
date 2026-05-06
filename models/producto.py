"""
models/producto.py
Representa un producto del menú (lo que se vende al cliente).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Producto:
    """
    Modelo que representa un producto del menú.

    Campos obligatorios al crear:
        nombre       — nombre único del producto (ej. "Hamburguesa Clásica")
        categoria    — agrupación para la UI (ej. "Hamburguesas", "Bebidas")
        precio_venta — precio al cliente

    Campos opcionales / gestionados:
        activo       — soft delete: False = no aparece en ventas
        id           — None hasta persistir
        created_at   — ISO-8601, asignado al crear
    """

    nombre: str
    categoria: str
    precio_venta: float

    activo: bool = True
    id: int | None = field(default=None)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # ------------------------------------------------------------------
    # Propiedades de dominio
    # ------------------------------------------------------------------

    @property
    def esta_disponible(self) -> bool:
        """True si el producto está activo y puede venderse."""
        return self.activo

    # ------------------------------------------------------------------
    # Conversión desde sqlite3.Row
    # ------------------------------------------------------------------

    @classmethod
    def from_row(cls, row) -> "Producto":
        return cls(
            id=row["id"],
            nombre=row["nombre"],
            categoria=row["categoria"],
            precio_venta=row["precio_venta"],
            activo=bool(row["activo"]),
            created_at=row["created_at"],
        )

    def __str__(self) -> str:
        estado = "activo" if self.activo else "INACTIVO"
        return (
            f"Producto(id={self.id}, nombre='{self.nombre}', "
            f"categoria='{self.categoria}', precio=${self.precio_venta:.2f}, {estado})"
        )
