"""
services/sales_service.py
Lógica de negocio para registrar ventas y descontar insumos automáticamente.

Convenciones:
  - No usa print(); lanza excepciones que la UI captura.
  - La transacción completa (venta + detalles + descuento de stock) ocurre
    dentro de un bloque atómico usando BEGIN / COMMIT explícitos para que,
    si falla cualquier paso, todo quede revertido.
  - Recibe repositorios por inyección de dependencias.
"""

import sqlite3
from typing import Any

from database.repositories.venta_repository import VentaRepository
from database.repositories.receta_repository import RecetaRepository
from database.repositories.insumo_repository import InsumoRepository
from models.venta import Venta


class StockInsuficienteError(Exception):
    """Se lanza cuando un producto no tiene suficiente stock de insumos."""


class ProductoNoActivoError(Exception):
    """Se lanza cuando se intenta vender un producto inactivo."""


class SalesService:
    """
    Servicio de ventas.

    Parámetros
    ----------
    conn : sqlite3.Connection
        Conexión activa (singleton del proyecto).
    venta_repo : VentaRepository
    receta_repo : RecetaRepository
    insumo_repo : InsumoRepository
    """

    METODOS_PAGO_VALIDOS = {"efectivo", "tarjeta", "transferencia"}

    def __init__(
        self,
        conn: sqlite3.Connection,
        venta_repo: VentaRepository,
        receta_repo: RecetaRepository,
        insumo_repo: InsumoRepository,
    ) -> None:
        self._conn = conn
        self._venta_repo = venta_repo
        self._receta_repo = receta_repo
        self._insumo_repo = insumo_repo

    # ================================================================== #
    # Método principal                                                    #
    # ================================================================== #

    def registrar_venta(
        self,
        items: list[dict[str, Any]],
        metodo_pago: str = "efectivo",
        descontar_insumos: bool = True,
    ) -> Venta:
        """
        Registra una venta completa de forma atómica.

        Parámetros
        ----------
        items : lista de dicts con:
            - 'producto_id'    : int
            - 'cantidad'       : int  (≥ 1)
            - 'precio_unitario': float
            - 'nombre'         : str  (opcional, solo para mensajes de error)
            - 'activo'         : bool (opcional, para validación previa)
        metodo_pago : 'efectivo' | 'tarjeta' | 'transferencia'
        descontar_insumos : si True, descuenta insumos según recetas al finalizar.

        Retorna
        -------
        Venta recién creada con su id.

        Lanza
        -----
        ValueError              — items vacíos o metodo_pago inválido.
        ProductoNoActivoError   — algún producto tiene activo=False.
        StockInsuficienteError  — stock insuficiente para cubrir la venta
                                  (solo si descontar_insumos=True).
        """
        # ── 1. Validaciones previas ─────────────────────────────────── #
        if not items:
            raise ValueError("La venta debe contener al menos un producto.")

        metodo_pago = metodo_pago.lower()
        if metodo_pago not in self.METODOS_PAGO_VALIDOS:
            raise ValueError(
                f"Método de pago inválido: '{metodo_pago}'. "
                f"Use: {', '.join(self.METODOS_PAGO_VALIDOS)}."
            )

        for item in items:
            if item.get("activo") is False:
                nombre = item.get("nombre", f"id={item['producto_id']}")
                raise ProductoNoActivoError(
                    f"El producto '{nombre}' está desactivado y no puede venderse."
                )
            if item["cantidad"] < 1:
                raise ValueError(
                    f"La cantidad del producto id={item['producto_id']} debe ser ≥ 1."
                )

        # ── 2. Verificar stock si aplica ────────────────────────────── #
        if descontar_insumos:
            self._verificar_stock_todos(items)

        # ── 3. Calcular total ───────────────────────────────────────── #
        total = sum(
            item["cantidad"] * item["precio_unitario"] for item in items
        )

        # ── 4. Transacción atómica ──────────────────────────────────── #
        try:
            self._conn.execute("BEGIN")

            # 4a. Insertar cabecera de venta
            cur = self._conn.execute(
                "INSERT INTO ventas (total, metodo_pago, descontar_insumos) VALUES (?, ?, ?)",
                (total, metodo_pago, int(descontar_insumos)),
            )
            venta_id = cur.lastrowid

            # 4b. Insertar detalles
            for item in items:
                self._conn.execute(
                    """
                    INSERT INTO detalle_ventas
                        (venta_id, producto_id, cantidad, precio_unitario)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        venta_id,
                        item["producto_id"],
                        item["cantidad"],
                        item["precio_unitario"],
                    ),
                )

            # 4c. Descontar insumos
            if descontar_insumos:
                self._descontar_insumos(items)

            self._conn.commit()

        except Exception:
            self._conn.rollback()
            raise

        # ── 5. Devolver el objeto Venta recién creado ───────────────── #
        venta = self._venta_repo.obtener(venta_id)
        return venta

    # ================================================================== #
    # Helpers privados                                                    #
    # ================================================================== #

    def _verificar_stock_todos(self, items: list[dict]) -> None:
        """
        Verifica que haya stock suficiente para TODOS los productos antes
        de iniciar la transacción.  Agrega cantidades si el mismo producto
        aparece más de una vez.

        Lanza StockInsuficienteError si alguno no tiene stock.
        """
        # Consolidar cantidades por producto
        totales: dict[int, int] = {}
        for item in items:
            pid = item["producto_id"]
            totales[pid] = totales.get(pid, 0) + item["cantidad"]

        for producto_id, cantidad_total in totales.items():
            faltantes = self._receta_repo.verificar_stock_para_producto(
                producto_id, cantidad_total
            )
            if faltantes:
                nombres_faltantes = ", ".join(
                    f"{f['nombre_insumo']} (faltan {f['faltante']:.2f} {f['unidad']})"
                    for f in faltantes
                )
                raise StockInsuficienteError(
                    f"Stock insuficiente para el producto id={producto_id}: "
                    f"{nombres_faltantes}."
                )

    def _descontar_insumos(self, items: list[dict]) -> None:
        """
        Descuenta los insumos de cada producto según su receta.
        Llama a InsumoRepository.actualizar_stock(id, delta) con delta negativo.

        Se ejecuta dentro de la transacción abierta por `registrar_venta`.
        """
        # Consolidar cantidades por producto
        totales: dict[int, int] = {}
        for item in items:
            pid = item["producto_id"]
            totales[pid] = totales.get(pid, 0) + item["cantidad"]

        for producto_id, cantidad_total in totales.items():
            recetas = self._receta_repo.listar_por_producto(producto_id)
            for receta in recetas:
                delta = -(receta.cantidad_requerida * cantidad_total)
                self._insumo_repo.actualizar_stock(receta.insumo_id, delta)
