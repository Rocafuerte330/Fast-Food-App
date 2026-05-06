"""
ui/inventory_view.py
Vista de Inventario — lista, alta, edición y eliminación de insumos.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

from database.repositories.insumo_repository import InsumoRepository
from models.insumo import Insumo


# ──────────────────────────────────────────────────────────────────────
# Colores y constantes de la vista
# ──────────────────────────────────────────────────────────────────────
COLOR_ALERTA = "#FF6B6B"
COLOR_OK = "#4CAF50"
COLOR_HEADER = "#2B2D42"
COLOR_ROW_EVEN = "#F0F0F0"
COLOR_ROW_ODD = "#FFFFFF"
COLOR_BAJO_STOCK = "#FFF3CD"
FUENTE_TABLA = ("Segoe UI", 12)
FUENTE_HEADER = ("Segoe UI", 12, "bold")
COLUMNAS = ["ID", "Nombre", "Unidad", "Stock", "Mín.", "Precio/U", "Valor total", "Estado"]
ANCHOS   = [40,   220,      80,       80,      60,     90,          95,            110]


# ──────────────────────────────────────────────────────────────────────
# Diálogo: Nuevo / Editar insumo
# ──────────────────────────────────────────────────────────────────────
class InsumoDialog(ctk.CTkToplevel):
    """
    Ventana modal para crear o editar un insumo.
    Al confirmar, llama a `on_save(insumo)` si la validación es exitosa.
    """

    def __init__(self, parent, on_save, insumo: Optional[Insumo] = None):
        super().__init__(parent)
        self.title("Nuevo insumo" if insumo is None else "Editar insumo")
        self.geometry("380x340")
        self.resizable(False, False)
        self.grab_set()                 # modal
        self.lift()

        self._on_save = on_save
        self._insumo = insumo

        self._build_form()
        if insumo:
            self._rellenar(insumo)

    # ------------------------------------------------------------------
    def _build_form(self):
        pad = {"padx": 18, "pady": 6}

        ctk.CTkLabel(self, text="Nombre *", anchor="w").pack(fill="x", **pad)
        self._e_nombre = ctk.CTkEntry(self, placeholder_text="Ej. Harina de trigo")
        self._e_nombre.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Unidad de medida *", anchor="w").pack(fill="x", **pad)
        self._e_unidad = ctk.CTkEntry(self, placeholder_text="kg / L / unidades")
        self._e_unidad.pack(fill="x", **pad)

        frame_nums = ctk.CTkFrame(self, fg_color="transparent")
        frame_nums.pack(fill="x", **pad)

        for col, (label, attr) in enumerate([
            ("Stock inicial *", "_e_stock"),
            ("Stock mínimo *", "_e_stock_min"),
            ("Precio/U *",     "_e_precio"),
        ]):
            ctk.CTkLabel(frame_nums, text=label).grid(row=0, column=col, padx=4, sticky="w")
            entry = ctk.CTkEntry(frame_nums, width=90)
            entry.grid(row=1, column=col, padx=4)
            setattr(self, attr, entry)

        frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        frame_btns.pack(fill="x", padx=18, pady=(14, 8))
        ctk.CTkButton(frame_btns, text="Cancelar", fg_color="gray50",
                      command=self.destroy).pack(side="left", padx=4)
        ctk.CTkButton(frame_btns, text="Guardar",
                      command=self._guardar).pack(side="right", padx=4)

    def _rellenar(self, insumo: Insumo):
        self._e_nombre.insert(0, insumo.nombre)
        self._e_unidad.insert(0, insumo.unidad)
        self._e_stock.insert(0, str(insumo.stock))
        self._e_stock_min.insert(0, str(insumo.stock_minimo))
        self._e_precio.insert(0, str(insumo.precio_unit))

    # ------------------------------------------------------------------
    def _guardar(self):
        # Lectura de campos
        nombre = self._e_nombre.get().strip()
        unidad = self._e_unidad.get().strip()
        raw = {
            "stock":      self._e_stock.get().strip(),
            "stock_min":  self._e_stock_min.get().strip(),
            "precio":     self._e_precio.get().strip(),
        }

        # Validaciones básicas
        if not nombre or not unidad:
            messagebox.showwarning("Campos requeridos", "Nombre y unidad son obligatorios.",
                                   parent=self)
            return

        try:
            stock     = float(raw["stock"])
            stock_min = float(raw["stock_min"])
            precio    = float(raw["precio"])
        except ValueError:
            messagebox.showwarning("Formato inválido",
                                   "Stock, mínimo y precio deben ser números.",
                                   parent=self)
            return

        if stock < 0 or stock_min < 0 or precio < 0:
            messagebox.showwarning("Valores inválidos",
                                   "Los valores numéricos no pueden ser negativos.",
                                   parent=self)
            return

        # Construir objeto
        if self._insumo is None:
            insumo = Insumo(nombre=nombre, unidad=unidad,
                            stock=stock, stock_minimo=stock_min, precio_unit=precio)
        else:
            self._insumo.nombre      = nombre
            self._insumo.unidad      = unidad
            self._insumo.stock       = stock
            self._insumo.stock_minimo = stock_min
            self._insumo.precio_unit = precio
            insumo = self._insumo

        self._on_save(insumo)
        self.destroy()


# ──────────────────────────────────────────────────────────────────────
# Vista principal de Inventario
# ──────────────────────────────────────────────────────────────────────
class InventoryView(ctk.CTkFrame):
    """
    Frame embebible en la ventana principal de la app.

    Uso:
        view = InventoryView(parent_frame, db_connection)
        view.pack(fill="both", expand=True)
    """

    def __init__(self, parent, db_connection):
        super().__init__(parent)
        self._repo = InsumoRepository(db_connection)
        self._insumo_seleccionado: Optional[Insumo] = None

        self._build_toolbar()
        self._build_alerta_banner()
        self._build_tabla()
        self._build_statusbar()

        self.cargar_insumos()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _build_toolbar(self):
        bar = ctk.CTkFrame(self, height=48, corner_radius=0)
        bar.pack(fill="x", padx=0, pady=(0, 2))

        ctk.CTkLabel(bar, text="📦  Inventario de Insumos",
                     font=("Segoe UI", 16, "bold")).pack(side="left", padx=16)

        btns = [
            ("＋  Nuevo",    self._abrir_nuevo),
            ("✏  Editar",    self._abrir_editar),
            ("🗑  Eliminar",  self._eliminar),
            ("🔄  Actualizar", self.cargar_insumos),
        ]
        for texto, cmd in reversed(btns):
            ctk.CTkButton(bar, text=texto, width=110, command=cmd).pack(
                side="right", padx=6, pady=8
            )

    def _build_alerta_banner(self):
        """Banner que se muestra sólo cuando hay insumos con bajo stock."""
        self._banner = ctk.CTkFrame(self, fg_color=COLOR_ALERTA, height=32,
                                    corner_radius=0)
        self._lbl_banner = ctk.CTkLabel(self._banner, text="",
                                        text_color="white",
                                        font=("Segoe UI", 11, "bold"))
        self._lbl_banner.pack(side="left", padx=12)
        # Se muestra u oculta en cargar_insumos()

    def _build_tabla(self):
        """Tabla con scrollbar usando tk.Canvas + Frame interior."""
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=10, pady=4)

        # Encabezados
        header = tk.Frame(container, bg=COLOR_HEADER)
        header.pack(fill="x")
        for col, (nombre, ancho) in enumerate(zip(COLUMNAS, ANCHOS)):
            tk.Label(header, text=nombre, font=FUENTE_HEADER,
                     bg=COLOR_HEADER, fg="white",
                     width=ancho // 8, anchor="center",
                     padx=4, pady=6).grid(row=0, column=col, sticky="nsew")
            header.columnconfigure(col, weight=1)

        # Canvas + Scrollbar para las filas
        wrapper = tk.Frame(container)
        wrapper.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(wrapper, highlightthickness=0)
        scrollbar = tk.Scrollbar(wrapper, orient="vertical",
                                 command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._frame_filas = tk.Frame(self._canvas)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._frame_filas, anchor="nw"
        )

        self._frame_filas.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, height=28, corner_radius=0)
        bar.pack(fill="x", side="bottom")
        self._lbl_status = ctk.CTkLabel(bar, text="", font=("Segoe UI", 11))
        self._lbl_status.pack(side="left", padx=12)

    # ------------------------------------------------------------------
    # Eventos de scroll
    # ------------------------------------------------------------------

    def _on_frame_configure(self, _event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ------------------------------------------------------------------
    # Carga y renderizado de datos
    # ------------------------------------------------------------------

    def cargar_insumos(self):
        """Recarga todos los insumos desde la DB y repinta la tabla."""
        try:
            insumos = self._repo.listar()
        except RuntimeError as exc:
            messagebox.showerror("Error de base de datos", str(exc))
            return

        self._insumos = insumos
        self._insumo_seleccionado = None
        self._renderizar_filas(insumos)
        self._actualizar_banner(insumos)
        self._actualizar_status(insumos)

    def _renderizar_filas(self, insumos: list[Insumo]):
        # Limpiar filas anteriores
        for widget in self._frame_filas.winfo_children():
            widget.destroy()
        self._filas_widgets = []

        for idx, ins in enumerate(insumos):
            bg = COLOR_BAJO_STOCK if ins.bajo_stock else (
                COLOR_ROW_EVEN if idx % 2 == 0 else COLOR_ROW_ODD
            )
            estado = "⚠ Bajo stock" if ins.bajo_stock else "✔ OK"
            valores = [
                str(ins.id),
                ins.nombre,
                ins.unidad,
                f"{ins.stock:,.2f}",
                f"{ins.stock_minimo:,.2f}",
                f"${ins.precio_unit:,.2f}",
                f"${ins.valor_total:,.2f}",
                estado,
            ]

            fila_widgets = []
            for col, (val, ancho) in enumerate(zip(valores, ANCHOS)):
                lbl = tk.Label(self._frame_filas, text=val,
                               font=FUENTE_TABLA, bg=bg,
                               width=ancho // 8, anchor="center",
                               padx=4, pady=5, cursor="hand2")
                lbl.grid(row=idx, column=col, sticky="nsew")
                self._frame_filas.columnconfigure(col, weight=1)
                lbl.bind("<Button-1>", lambda e, i=ins: self._seleccionar(i))
                fila_widgets.append(lbl)

            self._filas_widgets.append((ins, fila_widgets, bg))

    def _seleccionar(self, insumo: Insumo):
        """Marca la fila seleccionada visualmente."""
        self._insumo_seleccionado = insumo
        for ins, widgets, bg_original in self._filas_widgets:
            color = "#C8E6FA" if ins.id == insumo.id else bg_original
            for w in widgets:
                w.configure(bg=color)
        self._lbl_status.configure(
            text=f"Seleccionado: {insumo.nombre}  |  Stock: {insumo.stock} {insumo.unidad}"
        )

    def _actualizar_banner(self, insumos: list[Insumo]):
        alertas = [i for i in insumos if i.bajo_stock]
        if alertas:
            nombres = ", ".join(i.nombre for i in alertas[:3])
            extra = f" (+{len(alertas)-3} más)" if len(alertas) > 3 else ""
            self._lbl_banner.configure(
                text=f"⚠  Insumos con stock bajo: {nombres}{extra}"
            )
            self._banner.pack(fill="x", before=self._canvas.master.master
                              if hasattr(self._canvas, 'master') else self)
            self._banner.pack(fill="x")
        else:
            self._banner.pack_forget()

    def _actualizar_status(self, insumos: list[Insumo]):
        total = sum(i.valor_total for i in insumos)
        self._lbl_status.configure(
            text=f"{len(insumos)} insumos  |  Valor total inventario: ${total:,.2f}"
        )

    # ------------------------------------------------------------------
    # Acciones de la toolbar
    # ------------------------------------------------------------------

    def _abrir_nuevo(self):
        InsumoDialog(self, on_save=self._guardar_nuevo)

    def _guardar_nuevo(self, insumo: Insumo):
        try:
            self._repo.guardar(insumo)
            self.cargar_insumos()
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Error", str(exc))

    def _abrir_editar(self):
        if not self._insumo_seleccionado:
            messagebox.showinfo("Sin selección", "Selecciona un insumo para editar.")
            return
        InsumoDialog(self, on_save=self._guardar_edicion,
                     insumo=self._insumo_seleccionado)

    def _guardar_edicion(self, insumo: Insumo):
        try:
            self._repo.actualizar(insumo)
            self.cargar_insumos()
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Error", str(exc))

    def _eliminar(self):
        if not self._insumo_seleccionado:
            messagebox.showinfo("Sin selección", "Selecciona un insumo para eliminar.")
            return
        ins = self._insumo_seleccionado
        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar el insumo '{ins.nombre}'?\n"
            "Esta acción no se puede deshacer.",
        )
        if confirmar:
            try:
                self._repo.eliminar(ins.id)
                self.cargar_insumos()
            except (ValueError, RuntimeError) as exc:
                messagebox.showerror("Error", str(exc))
