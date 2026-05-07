"""
models/venta.py
Modelo de datos para una venta registrada en el sistema.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Venta:
    """Representa una venta completa registrada en la tabla `ventas`."""

    id: Optional[int]
    fecha: str
    total: float
    metodo_pago: str
    descontar_insumos: bool

    # Atributo enriquecido opcional (se llena si se hace JOIN con detalle_ventas)
    detalles: list = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Propiedades                                                          #
    # ------------------------------------------------------------------ #

    @property
    def metodo_pago_label(self) -> str:
        """Devuelve el método de pago formateado para mostrar en la UI."""
        labels = {
            "efectivo": "Efectivo",
            "tarjeta": "Tarjeta",
            "transferencia": "Transferencia",
        }
        return labels.get(self.metodo_pago, self.metodo_pago.capitalize())

    @property
    def total_fmt(self) -> str:
        """Total formateado como cadena con 2 decimales."""
        return f"${self.total:,.2f}"

    # ------------------------------------------------------------------ #
    # Constructor desde sqlite3.Row                                       #
    # ------------------------------------------------------------------ #

    @classmethod
    def from_row(cls, row) -> "Venta":
        """
        Crea una instancia a partir de un sqlite3.Row.
        `descontar_insumos` se almacena como INTEGER (0/1) y se convierte a bool.
        """
        return cls(
            id=row["id"],
            fecha=row["fecha"],
            total=row["total"],
            metodo_pago=row["metodo_pago"],
            descontar_insumos=bool(row["descontar_insumos"]),
        )
