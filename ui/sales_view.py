"""
ui/sales_view.py
Vista del Módulo de Ventas — CustomTkinter

Layout:
  ┌─────────────────────────────────────────────────────────────┐
  │  PANEL IZQUIERDO (catálogo)  │  PANEL DERECHO (carrito)     │
  │  Filtro categoría            │  Tabla de ítems              │
  │  Tabla de productos          │  Total + método de pago      │
  │  [+ Agregar al carrito]      │  [Registrar Venta]           │
  └─────────────────────────────────────────────────────────────┘

El historial de ventas se muestra en un tab separado (SalesHistoryFrame).
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import date

from database.repositories.producto_repository import ProductoRepository
from database.repositories.venta_repository import VentaRepository
from database.repositories.receta_repository import RecetaRepository
from database.repositories.insumo_repository import InsumoRepository
from services.sales_service import (
    SalesService,
    StockInsuficienteError,
    ProductoNoActivoError,
)


# ══════════════════════════════════════════════════════════════════════ #
#  Vista principal de Ventas                                            #
# ══════════════════════════════════════════════════════════════════════ #

class SalesView(ctk.CTkFrame):
    """
    Frame raíz del módulo de Ventas.
    Contiene dos tabs: «Nueva Venta» e «Historial».
    """

    def __init__(self, master, connection, **kwargs):
        super().__init__(master, **kwargs)

        self._conn = connection

        # Repositorios y servicio
        self._producto_repo = ProductoRepository(connection)
        self._venta_repo    = VentaRepository(connection)
        self._receta_repo   = RecetaRepository(connection)
        self._insumo_repo   = InsumoRepository(connection)
        self._sales_service = SalesService(
            connection,
            self._venta_repo,
            self._receta_repo,
            self._insumo_repo,
        )

        self._build_ui()

    # ------------------------------------------------------------------ #
    # Construcción de la UI                                               #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._tabview = ctk.CTkTabview(self)
        self._tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self._tabview.add("🛒  Nueva Venta")
        self._tabview.add("📋  Historial")

        # Tab 1 — Nueva venta
        nueva_tab = self._tabview.tab("🛒  Nueva Venta")
        nueva_tab.grid_rowconfigure(0, weight=1)
        nueva_tab.grid_columnconfigure(0, weight=3)
        nueva_tab.grid_columnconfigure(1, weight=2)

        self._catalog_frame = _CatalogFrame(
            nueva_tab,
            producto_repo=self._producto_repo,
            on_add_to_cart=self._on_add_to_cart,
        )
        self._catalog_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self._cart_frame = _CartFrame(
            nueva_tab,
            on_confirm=self._on_confirm_sale,
        )
        self._cart_frame.grid(row=0, column=1, sticky="nsew")

        # Tab 2 — Historial
        hist_tab = self._tabview.tab("📋  Historial")
        hist_tab.grid_rowconfigure(0, weight=1)
        hist_tab.grid_columnconfigure(0, weight=1)

        self._history_frame = _HistoryFrame(
            hist_tab,
            venta_repo=self._venta_repo,
        )
        self._history_frame.grid(row=0, column=0, sticky="nsew")

    # ------------------------------------------------------------------ #
    # Callbacks                                                           #
    # ------------------------------------------------------------------ #

    def _on_add_to_cart(self, producto: dict):
        """Recibe un producto del catálogo y lo agrega al carrito."""
        self._cart_frame.agregar_item(producto)

    def _on_confirm_sale(self, items: list[dict], metodo_pago: str, descontar: bool):
        """
        Llamado por _CartFrame cuando el usuario confirma la venta.
        Delega al servicio y actualiza el historial.
        """
        try:
            venta = self._sales_service.registrar_venta(
                items=items,
                metodo_pago=metodo_pago,
                descontar_insumos=descontar,
            )
            messagebox.showinfo(
                "Venta registrada",
                f"✅ Venta #{venta.id} registrada exitosamente.\n"
                f"Total: {venta.total_fmt}  —  {venta.metodo_pago_label}",
            )
            self._cart_frame.limpiar()
            self._history_frame.recargar()
            # Refrescar catálogo por si cambió el stock
            self._catalog_frame.recargar()

        except (StockInsuficienteError, ProductoNoActivoError, ValueError) as exc:
            messagebox.showerror("Error en la venta", str(exc))
        except Exception as exc:
            messagebox.showerror("Error inesperado", f"Ocurrió un error:\n{exc}")


# ══════════════════════════════════════════════════════════════════════ #
#  Panel izquierdo: Catálogo de productos                               #
# ══════════════════════════════════════════════════════════════════════ #

class _CatalogFrame(ctk.CTkFrame):
    """Muestra los productos activos con filtro por categoría."""

    def __init__(self, master, producto_repo: ProductoRepository, on_add_to_cart, **kwargs):
        super().__init__(master, **kwargs)

        self._repo = producto_repo
        self._on_add_to_cart = on_add_to_cart
        self._productos: list = []

        self._build_ui()
        self.recargar()

    def _build_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Título
        ctk.CTkLabel(self, text="Productos", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 4)
        )

        # Filtro de categoría
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
        filter_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(filter_frame, text="Categoría:").grid(row=0, column=0, padx=(0, 6))
        self._cat_var = ctk.StringVar(value="Todas")
        self._cat_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self._cat_var,
            values=["Todas"],
            command=self._on_filter,
            state="readonly",
        )
        self._cat_combo.grid(row=0, column=1, sticky="ew")

        # Tabla
        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 6))
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        cols = ("nombre", "categoria", "precio")
        self._tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        self._tree.heading("nombre",    text="Nombre")
        self._tree.heading("categoria", text="Categoría")
        self._tree.heading("precio",    text="Precio")
        self._tree.column("nombre",    width=200)
        self._tree.column("categoria", width=120)
        self._tree.column("precio",    width=80, anchor="e")
        self._tree.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")

        self._tree.bind("<Double-1>", lambda e: self._agregar_seleccionado())

        # Botón agregar
        ctk.CTkButton(self, text="＋  Agregar al carrito", command=self._agregar_seleccionado).grid(
            row=3, column=0, pady=(0, 10), padx=10, sticky="ew"
        )

    def recargar(self):
        """Recarga productos activos y actualiza el combo de categorías."""
        self._productos = self._repo.listar(solo_activos=True)

        categorias = sorted({p.categoria for p in self._productos})
        self._cat_combo.configure(values=["Todas"] + categorias)

        self._renderizar(self._productos)

    def _on_filter(self, _=None):
        cat = self._cat_var.get()
        if cat == "Todas":
            self._renderizar(self._productos)
        else:
            self._renderizar([p for p in self._productos if p.categoria == cat])

    def _renderizar(self, productos):
        self._tree.delete(*self._tree.get_children())
        for p in productos:
            self._tree.insert("", "end", iid=str(p.id), values=(
                p.nombre,
                p.categoria,
                f"${p.precio_venta:,.2f}",
            ))

    def _agregar_seleccionado(self):
        sel = self._tree.selection()
        if not sel:
            return
        pid = int(sel[0])
        producto = next((p for p in self._productos if p.id == pid), None)
        if producto:
            self._on_add_to_cart({
                "producto_id":    producto.id,
                "nombre":         producto.nombre,
                "precio_unitario": producto.precio_venta,
                "activo":         producto.esta_disponible(),
            })


# ══════════════════════════════════════════════════════════════════════ #
#  Panel derecho: Carrito / resumen de venta                            #
# ══════════════════════════════════════════════════════════════════════ #

class _CartFrame(ctk.CTkFrame):
    """Carrito de compras con total y confirmación de venta."""

    METODOS = ["efectivo", "tarjeta", "transferencia"]

    def __init__(self, master, on_confirm, **kwargs):
        super().__init__(master, **kwargs)
        self._on_confirm = on_confirm
        self._items: list[dict] = []  # {'producto_id', 'nombre', 'precio_unitario', 'cantidad', 'activo'}

        self._build_ui()

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Carrito", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 4)
        )

        # Tabla del carrito
        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 6))
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        cols = ("nombre", "cant", "precio", "subtotal")
        self._tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        self._tree.heading("nombre",   text="Producto")
        self._tree.heading("cant",     text="Cant.")
        self._tree.heading("precio",   text="P.Unit.")
        self._tree.heading("subtotal", text="Subtotal")
        self._tree.column("nombre",   width=150)
        self._tree.column("cant",     width=50,  anchor="center")
        self._tree.column("precio",   width=75,  anchor="e")
        self._tree.column("subtotal", width=75,  anchor="e")
        self._tree.grid(row=0, column=0, sticky="nsew")
        ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview).grid(
            row=0, column=1, sticky="ns"
        )

        # Botones de edición del carrito
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=2)
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(btn_frame, text="＋", width=40, command=self._incrementar).grid(row=0, column=0, padx=2)
        ctk.CTkButton(btn_frame, text="－", width=40, command=self._decrementar).grid(row=0, column=1, padx=2)
        ctk.CTkButton(btn_frame, text="🗑  Quitar", fg_color="#c0392b",
                      command=self._quitar_seleccionado).grid(row=0, column=2, padx=2, sticky="ew")

        # Total
        self._total_label = ctk.CTkLabel(
            self, text="Total: $0.00",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self._total_label.grid(row=3, column=0, sticky="e", padx=14, pady=4)

        # Método de pago
        pay_frame = ctk.CTkFrame(self, fg_color="transparent")
        pay_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=2)
        pay_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(pay_frame, text="Pago:").grid(row=0, column=0, padx=(0, 6))
        self._metodo_var = ctk.StringVar(value="efectivo")
        ctk.CTkComboBox(
            pay_frame,
            values=self.METODOS,
            variable=self._metodo_var,
            state="readonly",
        ).grid(row=0, column=1, sticky="ew")

        # Checkbox descontar insumos
        self._descontar_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self,
            text="Descontar insumos del stock",
            variable=self._descontar_var,
        ).grid(row=5, column=0, sticky="w", padx=12, pady=4)

        # Botón confirmar
        ctk.CTkButton(
            self,
            text="✔  Registrar Venta",
            fg_color="#27ae60",
            hover_color="#1e8449",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._confirmar,
        ).grid(row=6, column=0, sticky="ew", padx=10, pady=(4, 12))

    # ------------------------------------------------------------------ #
    # API pública                                                         #
    # ------------------------------------------------------------------ #

    def agregar_item(self, producto: dict):
        """Agrega o incrementa un producto en el carrito."""
        pid = producto["producto_id"]
        existente = next((i for i in self._items if i["producto_id"] == pid), None)
        if existente:
            existente["cantidad"] += 1
        else:
            self._items.append({**producto, "cantidad": 1})
        self._renderizar()

    def limpiar(self):
        self._items.clear()
        self._renderizar()

    # ------------------------------------------------------------------ #
    # Acciones                                                            #
    # ------------------------------------------------------------------ #

    def _incrementar(self):
        item = self._item_seleccionado()
        if item:
            item["cantidad"] += 1
            self._renderizar()

    def _decrementar(self):
        item = self._item_seleccionado()
        if item:
            if item["cantidad"] > 1:
                item["cantidad"] -= 1
            else:
                self._items.remove(item)
            self._renderizar()

    def _quitar_seleccionado(self):
        item = self._item_seleccionado()
        if item:
            self._items.remove(item)
            self._renderizar()

    def _confirmar(self):
        if not self._items:
            messagebox.showwarning("Carrito vacío", "Agregue al menos un producto al carrito.")
            return
        self._on_confirm(
            items=self._items,
            metodo_pago=self._metodo_var.get(),
            descontar=self._descontar_var.get(),
        )

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _item_seleccionado(self) -> dict | None:
        sel = self._tree.selection()
        if not sel:
            return None
        idx = int(sel[0])
        return self._items[idx] if idx < len(self._items) else None

    def _renderizar(self):
        self._tree.delete(*self._tree.get_children())
        total = 0.0
        for idx, item in enumerate(self._items):
            subtotal = item["cantidad"] * item["precio_unitario"]
            total += subtotal
            self._tree.insert("", "end", iid=str(idx), values=(
                item["nombre"],
                item["cantidad"],
                f"${item['precio_unitario']:,.2f}",
                f"${subtotal:,.2f}",
            ))
        self._total_label.configure(text=f"Total: ${total:,.2f}")


# ══════════════════════════════════════════════════════════════════════ #
#  Tab historial de ventas                                              #
# ══════════════════════════════════════════════════════════════════════ #

class _HistoryFrame(ctk.CTkFrame):
    """Muestra las ventas del día con filtro de fecha y detalle expandible."""

    def __init__(self, master, venta_repo: VentaRepository, **kwargs):
        super().__init__(master, **kwargs)
        self._repo = venta_repo
        self._build_ui()
        self.recargar()

    def _build_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Barra de filtro por fecha
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top, text="Fecha (YYYY-MM-DD):").grid(row=0, column=0, padx=(0, 6))
        self._fecha_entry = ctk.CTkEntry(top, placeholder_text=str(date.today()))
        self._fecha_entry.grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(top, text="🔍 Buscar", width=90, command=self._buscar).grid(
            row=0, column=2, padx=(6, 0)
        )
        ctk.CTkButton(top, text="↺ Hoy", width=70, command=self.recargar).grid(
            row=0, column=3, padx=(4, 0)
        )

        # Tabla de ventas
        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 4))
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        cols = ("id", "fecha", "total", "metodo", "insumos")
        self._tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
        self._tree.heading("id",      text="ID")
        self._tree.heading("fecha",   text="Fecha")
        self._tree.heading("total",   text="Total")
        self._tree.heading("metodo",  text="Método")
        self._tree.heading("insumos", text="Insumos desc.")
        self._tree.column("id",      width=40,  anchor="center")
        self._tree.column("fecha",   width=160)
        self._tree.column("total",   width=90,  anchor="e")
        self._tree.column("metodo",  width=110, anchor="center")
        self._tree.column("insumos", width=100, anchor="center")
        self._tree.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")

        self._tree.bind("<Double-1>", self._ver_detalle)

        # Resumen del día
        self._resumen_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=13, weight="bold")
        )
        self._resumen_label.grid(row=2, column=0, sticky="e", padx=14, pady=6)

    # ------------------------------------------------------------------ #

    def recargar(self):
        """Carga las ventas del día actual."""
        hoy = str(date.today())
        ventas = self._repo.listar_por_rango(hoy + "T00:00:00", hoy + "T23:59:59")
        self._renderizar(ventas)
        total_dia = self._repo.total_del_dia(hoy)
        self._resumen_label.configure(
            text=f"Total del día ({hoy}): ${total_dia:,.2f}"
        )

    def _buscar(self):
        fecha = self._fecha_entry.get().strip()
        if not fecha:
            self.recargar()
            return
        ventas = self._repo.listar_por_rango(fecha + "T00:00:00", fecha + "T23:59:59")
        self._renderizar(ventas)
        total = sum(v.total for v in ventas)
        self._resumen_label.configure(
            text=f"Total del día ({fecha}): ${total:,.2f}"
        )

    def _renderizar(self, ventas):
        self._tree.delete(*self._tree.get_children())
        for v in ventas:
            self._tree.insert("", "end", iid=str(v.id), values=(
                v.id,
                v.fecha[:19].replace("T", " "),
                v.total_fmt,
                v.metodo_pago_label,
                "✅ Sí" if v.descontar_insumos else "❌ No",
            ))

    def _ver_detalle(self, _event=None):
        sel = self._tree.selection()
        if not sel:
            return
        venta_id = int(sel[0])
        detalles = self._repo.listar_detalles(venta_id)
        _DetalleDialog(self, venta_id=venta_id, detalles=detalles)


# ══════════════════════════════════════════════════════════════════════ #
#  Diálogo de detalle de una venta                                      #
# ══════════════════════════════════════════════════════════════════════ #

class _DetalleDialog(ctk.CTkToplevel):
    """Ventana modal que muestra los ítems de una venta."""

    def __init__(self, master, venta_id: int, detalles, **kwargs):
        super().__init__(master, **kwargs)
        self.title(f"Detalle — Venta #{venta_id}")
        self.geometry("520x360")
        self.grab_set()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        cols = ("nombre", "cant", "precio", "subtotal")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        tree.heading("nombre",   text="Producto")
        tree.heading("cant",     text="Cant.")
        tree.heading("precio",   text="P.Unit.")
        tree.heading("subtotal", text="Subtotal")
        tree.column("nombre",   width=200)
        tree.column("cant",     width=60, anchor="center")
        tree.column("precio",   width=90, anchor="e")
        tree.column("subtotal", width=90, anchor="e")
        tree.grid(row=0, column=0, sticky="nsew")
        ttk.Scrollbar(frame, orient="vertical", command=tree.yview).grid(row=0, column=1, sticky="ns")

        total = 0.0
        for d in detalles:
            tree.insert("", "end", values=(
                d.nombre_producto or f"id={d.producto_id}",
                d.cantidad,
                d.precio_unitario_fmt,
                d.subtotal_fmt,
            ))
            total += d.subtotal

        ctk.CTkLabel(self, text=f"Total: ${total:,.2f}",
                     font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=1, column=0, sticky="e", padx=14, pady=4
        )
        ctk.CTkButton(self, text="Cerrar", command=self.destroy).grid(
            row=2, column=0, pady=(0, 10)
        )
