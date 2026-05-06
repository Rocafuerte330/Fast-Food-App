"""
ui/products_view.py
Vista de Productos y Recetas — lista, alta, edición, soft-delete y gestión de receta.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

from database.repositories.producto_repository import ProductoRepository
from database.repositories.receta_repository import RecetaRepository
from database.repositories.insumo_repository import InsumoRepository
from models.producto import Producto
from models.receta import Receta


# ──────────────────────────────────────────────────────────────────────
# Constantes de diseño
# ──────────────────────────────────────────────────────────────────────
COLOR_HEADER    = "#2B2D42"
COLOR_ROW_EVEN  = "#BBCF38"
COLOR_ROW_ODD   = "#41BCCC"
COLOR_INACTIVO  = "#2FB36C"
COLOR_SELECCION = "#2F7BAE"
COLOR_FALTANTE  = "#DD5C5C"
FUENTE_TABLA    = ("Segoe UI", 12)
FUENTE_HEADER   = ("Segoe UI", 12, "bold")

COLS_PRODUCTOS = ["ID", "Nombre", "Categoría", "Precio venta", "Estado"]
ANCHOS_PROD    = [40,   260,      150,          110,            90]

COLS_RECETA = ["Insumo", "Unidad", "Cantidad", "Stock actual", "Estado"]
ANCHOS_REC  = [200,       80,       90,          110,            100]


# ──────────────────────────────────────────────────────────────────────
# Diálogo: Nuevo / Editar Producto
# ──────────────────────────────────────────────────────────────────────
class ProductoDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_save, categorias: list[str],
                 producto: Optional[Producto] = None):
        super().__init__(parent)
        self.title("Nuevo producto" if producto is None else "Editar producto")
        self.geometry("500x500")
        self.resizable(False, False)
        self.grab_set()
        self.lift()

        self._on_save = on_save
        self._producto = producto
        self._categorias = categorias

        self._build()
        if producto:
            self._rellenar(producto)

    def _build(self):
        pad = {"padx": 18, "pady": 6}

        ctk.CTkLabel(self, text="Nombre *", anchor="w").pack(fill="x", **pad)
        self._e_nombre = ctk.CTkEntry(self, placeholder_text="Ej. Hamburguesa Clásica")
        self._e_nombre.pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Categoría *", anchor="w").pack(fill="x", **pad)
        # Permite escribir una nueva categoría o elegir una existente
        self._e_categoria = ctk.CTkEntry(self, placeholder_text="Ej. Hamburguesas")
        self._e_categoria.pack(fill="x", **pad)
        if self._categorias:
            sugerencias = "  |  ".join(self._categorias)
            ctk.CTkLabel(self, text=f"Existentes: {sugerencias}",
                         font=("Segoe UI", 10), text_color="gray").pack(
                fill="x", padx=18, pady=(0, 4))

        ctk.CTkLabel(self, text="Precio de venta *", anchor="w").pack(fill="x", **pad)
        self._e_precio = ctk.CTkEntry(self, placeholder_text="0.00")
        self._e_precio.pack(fill="x", **pad)

        self._var_activo = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self, text="Producto activo",
                        variable=self._var_activo).pack(padx=18, pady=6, anchor="w")

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=18, pady=(10, 8))
        ctk.CTkButton(frame, text="Cancelar", fg_color="gray50",
                      command=self.destroy).pack(side="left", padx=4)
        ctk.CTkButton(frame, text="Guardar",
                      command=self._guardar).pack(side="right", padx=4)

    def _rellenar(self, p: Producto):
        self._e_nombre.insert(0, p.nombre)
        self._e_categoria.insert(0, p.categoria)
        self._e_precio.insert(0, str(p.precio_venta))
        self._var_activo.set(p.activo)

    def _guardar(self):
        nombre    = self._e_nombre.get().strip()
        categoria = self._e_categoria.get().strip()
        raw_precio = self._e_precio.get().strip()

        if not nombre or not categoria:
            messagebox.showwarning("Campos requeridos",
                                   "Nombre y categoría son obligatorios.", parent=self)
            return
        try:
            precio = float(raw_precio)
        except ValueError:
            messagebox.showwarning("Formato inválido",
                                   "El precio debe ser un número.", parent=self)
            return
        if precio < 0:
            messagebox.showwarning("Valor inválido",
                                   "El precio no puede ser negativo.", parent=self)
            return

        if self._producto is None:
            prod = Producto(nombre=nombre, categoria=categoria, precio_venta=precio,
                            activo=self._var_activo.get())
        else:
            self._producto.nombre      = nombre
            self._producto.categoria   = categoria
            self._producto.precio_venta = precio
            self._producto.activo      = self._var_activo.get()
            prod = self._producto

        self._on_save(prod)
        self.destroy()


# ──────────────────────────────────────────────────────────────────────
# Diálogo: Gestión de Receta de un Producto
# ──────────────────────────────────────────────────────────────────────
class RecetaDialog(ctk.CTkToplevel):
    """
    Muestra y edita las líneas de receta de un producto.
    Permite agregar nuevas líneas y eliminar existentes.
    """

    def __init__(self, parent, producto: Producto,
                 receta_repo: RecetaRepository, insumo_repo: InsumoRepository):
        super().__init__(parent)
        self.title(f"Receta — {producto.nombre}")
        self.geometry("620x480")
        self.grab_set()
        self.lift()

        self._producto     = producto
        self._receta_repo  = receta_repo
        self._insumo_repo  = insumo_repo

        self._build()
        self._cargar_receta()

    # ------------------------------------------------------------------
    def _build(self):
        # Encabezado
        ctk.CTkLabel(self, text=f"📋  Receta de: {self._producto.nombre}",
                     font=("Segoe UI", 14, "bold")).pack(padx=16, pady=(12, 4), anchor="w")

        # Tabla de receta actual
        frame_tabla = ctk.CTkFrame(self)
        frame_tabla.pack(fill="both", expand=True, padx=12, pady=4)

        header = tk.Frame(frame_tabla, bg=COLOR_HEADER)
        header.pack(fill="x")
        for col, (nombre, ancho) in enumerate(zip(COLS_RECETA, ANCHOS_REC)):
            tk.Label(header, text=nombre, font=FUENTE_HEADER,
                     bg=COLOR_HEADER, fg="white",
                     width=ancho // 8, anchor="center", padx=4, pady=5
                     ).grid(row=0, column=col, sticky="nsew")
            header.columnconfigure(col, weight=1)

        self._frame_filas = tk.Frame(frame_tabla)
        self._frame_filas.pack(fill="both", expand=True)

        # Formulario para agregar línea
        sep = ctk.CTkFrame(self, height=2, fg_color="gray70")
        sep.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(self, text="Agregar ingrediente:",
                     font=("Segoe UI", 12, "bold")).pack(padx=16, anchor="w")

        frame_add = ctk.CTkFrame(self, fg_color="transparent")
        frame_add.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(frame_add, text="Insumo").grid(row=0, column=0, padx=4, sticky="w")
        ctk.CTkLabel(frame_add, text="Cantidad").grid(row=0, column=1, padx=4, sticky="w")

        self._combo_insumo = ctk.CTkComboBox(frame_add, width=240, values=[])
        self._combo_insumo.grid(row=1, column=0, padx=4, pady=2)

        self._e_cantidad = ctk.CTkEntry(frame_add, width=100,
                                         placeholder_text="ej. 0.15")
        self._e_cantidad.grid(row=1, column=1, padx=4, pady=2)

        ctk.CTkButton(frame_add, text="＋ Agregar", width=100,
                      command=self._agregar_linea).grid(row=1, column=2, padx=8)

        self._cargar_combo_insumos()

    def _cargar_combo_insumos(self):
        try:
            insumos = self._insumo_repo.listar()
            self._mapa_insumos = {
                f"{i.nombre} ({i.unidad})": i for i in insumos
            }
            self._combo_insumo.configure(values=list(self._mapa_insumos.keys()))
            if self._mapa_insumos:
                self._combo_insumo.set(list(self._mapa_insumos.keys())[0])
        except RuntimeError as exc:
            messagebox.showerror("Error", str(exc), parent=self)

    def _cargar_receta(self):
        for w in self._frame_filas.winfo_children():
            w.destroy()

        try:
            lineas = self._receta_repo.listar_por_producto(self._producto.id)
        except RuntimeError as exc:
            messagebox.showerror("Error", str(exc), parent=self)
            return

        if not lineas:
            tk.Label(self._frame_filas,
                     text="Sin ingredientes todavía. Agrega uno abajo.",
                     font=FUENTE_TABLA, fg="gray", pady=10).pack()
            return

        for idx, linea in enumerate(lineas):
            bg = COLOR_FALTANTE if not linea.insumo_disponible else (
                COLOR_ROW_EVEN if idx % 2 == 0 else COLOR_ROW_ODD
            )
            estado = "⚠ Sin stock" if not linea.insumo_disponible else "✔ OK"
            valores = [
                linea.nombre_insumo or "—",
                linea.unidad_insumo or "—",
                str(linea.cantidad_requerida),
                f"{linea.stock_insumo:.2f}" if linea.stock_insumo is not None else "—",
                estado,
            ]
            for col, (val, ancho) in enumerate(zip(valores, ANCHOS_REC)):
                tk.Label(self._frame_filas, text=val, font=FUENTE_TABLA,
                         bg=bg, width=ancho // 8, anchor="center",
                         padx=4, pady=4).grid(row=idx, column=col, sticky="nsew")
                self._frame_filas.columnconfigure(col, weight=1)

            # Botón eliminar por fila
            btn = tk.Button(self._frame_filas, text="✕", bg=bg,
                            relief="flat", cursor="hand2",
                            command=lambda lid=linea.id: self._eliminar_linea(lid))
            btn.grid(row=idx, column=len(COLS_RECETA), padx=4)

    def _agregar_linea(self):
        clave = self._combo_insumo.get()
        if clave not in self._mapa_insumos:
            messagebox.showwarning("Sin selección",
                                   "Selecciona un insumo válido.", parent=self)
            return
        try:
            cantidad = float(self._e_cantidad.get().strip())
        except ValueError:
            messagebox.showwarning("Formato inválido",
                                   "La cantidad debe ser un número.", parent=self)
            return

        insumo = self._mapa_insumos[clave]
        receta = Receta(producto_id=self._producto.id,
                        insumo_id=insumo.id,
                        cantidad_requerida=cantidad)
        try:
            self._receta_repo.guardar(receta)
            self._e_cantidad.delete(0, "end")
            self._cargar_receta()
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Error", str(exc), parent=self)

    def _eliminar_linea(self, receta_id: int):
        if messagebox.askyesno("Confirmar", "¿Eliminar este ingrediente de la receta?",
                               parent=self):
            try:
                self._receta_repo.eliminar(receta_id)
                self._cargar_receta()
            except (ValueError, RuntimeError) as exc:
                messagebox.showerror("Error", str(exc), parent=self)


# ──────────────────────────────────────────────────────────────────────
# Vista principal de Productos
# ──────────────────────────────────────────────────────────────────────
class ProductsView(ctk.CTkFrame):
    """
    Frame embebible en la ventana principal.

    Uso:
        view = ProductsView(parent_frame, db_connection)
        view.pack(fill="both", expand=True)
    """

    def __init__(self, parent, db_connection):
        super().__init__(parent)
        self._prod_repo   = ProductoRepository(db_connection)
        self._receta_repo = RecetaRepository(db_connection)
        self._insumo_repo = InsumoRepository(db_connection)
        self._seleccionado: Optional[Producto] = None

        self._build_toolbar()
        self._build_filtro()
        self._build_tabla()
        self._build_statusbar()

        self.cargar_productos()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _build_toolbar(self):
        bar = ctk.CTkFrame(self, height=48, corner_radius=0)
        bar.pack(fill="x", padx=0, pady=(0, 2))

        ctk.CTkLabel(bar, text="🍔  Productos y Recetas",
                     font=("Segoe UI", 16, "bold")).pack(side="left", padx=16)

        btns = [
            ("＋  Nuevo",       self._abrir_nuevo),
            ("✏  Editar",       self._abrir_editar),
            ("📋  Receta",      self._abrir_receta),
            ("⊘  Desactivar",   self._toggle_activo),
            ("🔄  Actualizar",  self.cargar_productos),
        ]
        for texto, cmd in reversed(btns):
            ctk.CTkButton(bar, text=texto, width=115, command=cmd).pack(
                side="right", padx=5, pady=8)

    def _build_filtro(self):
        bar = ctk.CTkFrame(self, height=36, corner_radius=0, fg_color="gray90")
        bar.pack(fill="x")

        ctk.CTkLabel(bar, text="Filtrar por categoría:",
                     text_color="gray20").pack(side="left", padx=12)
        self._filtro_var = ctk.StringVar(value="Todas")
        self._combo_filtro = ctk.CTkComboBox(
            bar, variable=self._filtro_var, width=200,
            values=["Todas"],
            command=lambda _: self.cargar_productos()
        )
        self._combo_filtro.pack(side="left", padx=6, pady=4)

        self._var_solo_activos = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(bar, text="Solo activos",
                        variable=self._var_solo_activos,
                        command=self.cargar_productos).pack(side="left", padx=16)

    def _build_tabla(self):
        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=10, pady=4)

        header = tk.Frame(container, bg=COLOR_HEADER)
        header.pack(fill="x")
        for col, (nombre, ancho) in enumerate(zip(COLS_PRODUCTOS, ANCHOS_PROD)):
            tk.Label(header, text=nombre, font=FUENTE_HEADER,
                     bg=COLOR_HEADER, fg="white",
                     width=ancho // 8, anchor="center",
                     padx=4, pady=6).grid(row=0, column=col, sticky="nsew")
            header.columnconfigure(col, weight=1)

        wrapper = tk.Frame(container)
        wrapper.pack(fill="both", expand=True)
        self._canvas = tk.Canvas(wrapper, highlightthickness=0)
        sb = tk.Scrollbar(wrapper, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._frame_filas = tk.Frame(self._canvas)
        self._cw = self._canvas.create_window((0, 0), window=self._frame_filas,
                                               anchor="nw")
        self._frame_filas.bind("<Configure>",
                               lambda e: self._canvas.configure(
                                   scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                          lambda e: self._canvas.itemconfig(self._cw, width=e.width))
        self._canvas.bind_all("<MouseWheel>",
                              lambda e: self._canvas.yview_scroll(
                                  int(-1 * (e.delta / 120)), "units"))

    def _build_statusbar(self):
        bar = ctk.CTkFrame(self, height=28, corner_radius=0)
        bar.pack(fill="x", side="bottom")
        self._lbl_status = ctk.CTkLabel(bar, text="", font=("Segoe UI", 11))
        self._lbl_status.pack(side="left", padx=12)

    # ------------------------------------------------------------------
    # Carga y render
    # ------------------------------------------------------------------

    def cargar_productos(self, *_):
        try:
            solo_activos = self._var_solo_activos.get()
            productos = self._prod_repo.listar(solo_activos=solo_activos)

            # Actualizar combo de categorías
            categorias = ["Todas"] + self._prod_repo.listar_categorias()
            self._combo_filtro.configure(values=categorias)

            # Filtrar por categoría seleccionada
            filtro = self._filtro_var.get()
            if filtro and filtro != "Todas":
                productos = [p for p in productos if p.categoria == filtro]

        except RuntimeError as exc:
            messagebox.showerror("Error de base de datos", str(exc))
            return

        self._productos = productos
        self._seleccionado = None
        self._renderizar(productos)
        self._lbl_status.configure(
            text=f"{len(productos)} producto(s) mostrado(s)"
        )

    def _renderizar(self, productos: list[Producto]):
        for w in self._frame_filas.winfo_children():
            w.destroy()
        self._filas = []

        for idx, prod in enumerate(productos):
            if not prod.activo:
                bg = COLOR_INACTIVO
            else:
                bg = COLOR_ROW_EVEN if idx % 2 == 0 else COLOR_ROW_ODD

            estado = "✔ Activo" if prod.activo else "✗ Inactivo"
            valores = [
                str(prod.id),
                prod.nombre,
                prod.categoria,
                f"${prod.precio_venta:.2f}",
                estado,
            ]
            fila_ws = []
            for col, (val, ancho) in enumerate(zip(valores, ANCHOS_PROD)):
                lbl = tk.Label(self._frame_filas, text=val, font=FUENTE_TABLA,
                               bg=bg, width=ancho // 8, anchor="center",
                               padx=4, pady=5, cursor="hand2")
                lbl.grid(row=idx, column=col, sticky="nsew")
                self._frame_filas.columnconfigure(col, weight=1)
                lbl.bind("<Button-1>", lambda e, p=prod: self._seleccionar(p))
                fila_ws.append(lbl)
            self._filas.append((prod, fila_ws, bg))

    def _seleccionar(self, prod: Producto):
        self._seleccionado = prod
        for p, ws, bg in self._filas:
            color = COLOR_SELECCION if p.id == prod.id else bg
            for w in ws:
                w.configure(bg=color)
        self._lbl_status.configure(
            text=f"Seleccionado: {prod.nombre}  |  {prod.categoria}  |  ${prod.precio_venta:.2f}"
        )

    # ------------------------------------------------------------------
    # Acciones de toolbar
    # ------------------------------------------------------------------

    def _abrir_nuevo(self):
        categorias = self._prod_repo.listar_categorias()
        ProductoDialog(self, on_save=self._guardar_nuevo, categorias=categorias)

    def _guardar_nuevo(self, prod: Producto):
        try:
            self._prod_repo.guardar(prod)
            self.cargar_productos()
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Error", str(exc))

    def _abrir_editar(self):
        if not self._seleccionado:
            messagebox.showinfo("Sin selección", "Selecciona un producto para editar.")
            return
        categorias = self._prod_repo.listar_categorias()
        ProductoDialog(self, on_save=self._guardar_edicion,
                       categorias=categorias, producto=self._seleccionado)

    def _guardar_edicion(self, prod: Producto):
        try:
            self._prod_repo.actualizar(prod)
            self.cargar_productos()
        except (ValueError, RuntimeError) as exc:
            messagebox.showerror("Error", str(exc))

    def _abrir_receta(self):
        if not self._seleccionado:
            messagebox.showinfo("Sin selección",
                                "Selecciona un producto para gestionar su receta.")
            return
        RecetaDialog(self, self._seleccionado, self._receta_repo, self._insumo_repo)

    def _toggle_activo(self):
        if not self._seleccionado:
            messagebox.showinfo("Sin selección", "Selecciona un producto.")
            return
        prod = self._seleccionado
        nuevo_estado = not prod.activo
        accion = "activar" if nuevo_estado else "desactivar"
        if messagebox.askyesno("Confirmar",
                               f"¿{accion.capitalize()} '{prod.nombre}'?"):
            try:
                self._prod_repo.cambiar_estado(prod.id, nuevo_estado)
                self.cargar_productos()
            except (ValueError, RuntimeError) as exc:
                messagebox.showerror("Error", str(exc))
