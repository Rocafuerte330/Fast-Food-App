# 🧾 Estado del Proyecto — Fast Food App

**Sesión:** #5  |  **Fecha:** 2026-05-06
**Colaboradora:** [Wendy Ortega] vía Git — rama activa: `main`

---

### Stack
- GUI: CustomTkinter | DB: SQLite | Reportes: openpyxl + reportlab
- Python: 3.11+ | Entorno: venv (`/venv`) | SO probado: macOS ✅

---

### Módulos — estado actual

| Módulo                                            | Estado       | Notas rápidas                                                |
|---------------------------------------------------|--------------|--------------------------------------------------------------|
| `database/schema.py`                              | ✅ Completo  | SQL_SCHEMA con 6 tablas + índices                            |
| `database/connection.py`                          | ✅ Completo  | Singleton, row_factory, PRAGMA foreign_keys ON               |
| `database/repositories/insumo_repository.py`      | ✅ Completo  | CRUD + actualizar_stock(delta) + listar_bajo_stock           |
| `database/repositories/producto_repository.py`    | ✅ Completo  | CRUD + cambiar_estado + listar_categorias                    |
| `database/repositories/receta_repository.py`      | ✅ Completo  | CRUD + verificar_stock_para_producto + eliminar_por_producto |
| `database/repositories/venta_repository.py`       | ✅ Completo  | crear, obtener, listar, listar_por_rango, eliminar, total_del_dia, agregar_detalle, listar_detalles, productos_mas_vendidos |
| `models/insumo.py`                                | ✅ Completo  | @dataclass, bajo_stock, valor_total, from_row()              |
| `models/producto.py`                              | ✅ Completo  | @dataclass, esta_disponible, activo como bool                |
| `models/receta.py`                                | ✅ Completo  | @dataclass, campos enriquecidos JOIN, insumo_disponible      |
| `models/venta.py`                                 | ✅ Completo  | @dataclass, metodo_pago_label, total_fmt, from_row()         |
| `models/detalle_venta.py`                         | ✅ Completo  | @dataclass, subtotal, from_row() con campos JOIN opcionales  |
| `services/inventory_service.py`                   | ⏳ Pendiente | Alerta de stock mínimo desacoplada de la UI                  |
| `services/sales_service.py`                       | ✅ Completo  | registrar_venta() atómico + descuento de insumos + errores tipados |
| `services/accounting`                             | ⏳ Pendiente |                                                              |
| `services/report`                                 | ⏳ Pendiente | Excel (openpyxl) + PDF (reportlab)                           |
| `ui/inventory_view.py`                            | ✅ Completo  | Tabla scroll, banner alertas, modal CRUD                     |
| `ui/products_view.py`                             | ✅ Completo  | Tabla scroll, filtro categoría, modal receta, soft-delete    |
| `ui/sales_view.py`                                | ✅ Completo  | Catálogo + carrito + historial + detalle modal               |
| `ui/accounting_view.py`                           | ⏳ Pendiente |                                                              |
| `main.py`                                         | ✅ Completo  | Ventana CTk base + botón Test DB funcionando                 |

---

### Última tarea completada

> **Fase 4 — Módulo de Ventas (Sesión #5):** Se implementaron los 5 módulos
> del módulo de ventas:
>
> - `models/venta.py` — `@dataclass` con `metodo_pago_label`, `total_fmt`, `from_row()`.
> - `models/detalle_venta.py` — `@dataclass` con `subtotal`, campos JOIN opcionales,
>   `from_row()` con detección automática de columnas enriquecidas.
> - `database/repositories/venta_repository.py` — CRUD completo (`crear`, `obtener`,
>   `listar`, `listar_por_rango`, `eliminar`, `total_del_dia`, `agregar_detalle`,
>   `listar_detalles` con JOIN, `productos_mas_vendidos`).
> - `services/sales_service.py` — `registrar_venta()` atómico con `BEGIN/ROLLBACK`,
>   validación previa de stock mediante `RecetaRepository.verificar_stock_para_producto`,
>   descuento de insumos vía `InsumoRepository.actualizar_stock(delta negativo)`.
>   Excepciones tipadas: `StockInsuficienteError`, `ProductoNoActivoError`.
> - `ui/sales_view.py` — `SalesView` con dos tabs:
>   «Nueva Venta» (catálogo filtrable + carrito con `+/-`/quitar) e
>   «Historial» (filtro por fecha, resumen diario, doble clic → `_DetalleDialog`).

---

### Pruebas realizadas

| Prueba                                          | Resultado |
|-------------------------------------------------|-----------|
| Creación automática de `fast_food.db`           | ✅ OK     |
| Inicialización de 6 tablas vía schema           | ✅ OK     |
| PRAGMA foreign_keys activo                      | ✅ OK     |
| Botón "Test DB" en ventana CTk                  | ✅ OK     |
| Entorno: macOS                                  | ✅ OK     |
| Insumo.from_row() con sqlite3.Row               | ✅ OK     |
| InsumoRepository — CRUD completo                | ✅ OK     |
| InventoryView — render y scroll                 | ✅ OK     |
| ProductoRepository — CRUD + soft-delete         | ✅ OK     |
| RecetaRepository — CRUD + verificar_stock       | ✅ OK     |
| ProductsView — filtro, receta, toggle activo    | ✅ OK     |
| VentaRepository — pendiente prueba              | ⏳        |
| SalesService — pendiente prueba                 | ⏳        |
| SalesView — pendiente prueba                    | ⏳        |

---

### Bloqueantes / decisiones pendientes

1. ~~Definir si `models/` usará `dataclasses` estándar o con validación adicional.~~ → **Resuelto:** `@dataclass` estándar de Python.
2. Decidir pantalla de inicio: ¿menú lateral fijo o navegación por tabs?

---

### Próximo objetivo

> **Fase 5 — Contabilidad y Reportes:** Implementar `services/inventory_service.py`
> (alertas de stock desacopladas de la UI), `services/accounting/` (resumen de ingresos
> y costos), `services/report/` (exportar a Excel con openpyxl y a PDF con reportlab),
> y `ui/accounting_view.py`.

---

### Convenciones acordadas

- Los repositorios reciben `db_connection` por inyección (no la crean internamente).
- Fechas en ISO-8601: `datetime.now().isoformat()` en Python / `datetime('now')` en SQLite.
- Los servicios no usan `print()` — lanzan excepciones que la UI captura.
- `row_factory = sqlite3.Row` activo: acceso a columnas por nombre.
- Archivo `.db` en `.gitignore` — no se versiona.
- `@dataclass` estándar para todos los modelos (sin librerías de validación externas).
- `actualizar_stock(id, delta)` acepta positivo (entrada) y negativo (salida) — patrón para ventas y compras.
- `activo` se almacena como `INTEGER` (0/1) en SQLite y se convierte a `bool` en `from_row()`.
- Campos enriquecidos de JOIN van en el modelo como atributos opcionales (`None` si no se hizo JOIN).
- Soft-delete en `productos`: usar `cambiar_estado()`, nunca `eliminar()` si tiene ventas.
- La lógica de descuento de insumos al vender vive en `sales_service.py`, no en la UI ni en el repositorio.
- Las transacciones de venta usan `BEGIN` / `COMMIT` / `ROLLBACK` explícitos en el servicio.
- Errores de negocio se comunican con excepciones tipadas (`StockInsuficienteError`, `ProductoNoActivoError`).

---

## 🗄️ Esquema de Base de Datos

> Referencia completa del `SQL_SCHEMA` en `database/schema.py`.
> **No modificar sin actualizar este documento.**

### Diagrama de relaciones

```
insumos ──────────────────────────────────────────────────────┐
  │ id (PK)                                                    │
  │ nombre (UNIQUE)                                            │
  │ unidad, stock, stock_minimo, precio_unit                   │
  │ created_at, updated_at                                     │
  │                                                            │
  ├──< recetas.insumo_id (ON DELETE RESTRICT)                  │
  │                                                            │
  └──< compras.insumo_id (ON DELETE RESTRICT) ─────────────────┘

productos
  │ id (PK)
  │ nombre (UNIQUE)
  │ categoria, precio_venta, activo
  │ created_at
  │
  ├──< recetas.producto_id (ON DELETE CASCADE)
  └──< detalle_ventas.producto_id (ON DELETE RESTRICT)

ventas
  │ id (PK)
  │ fecha, total, metodo_pago
  │ descontar_insumos (flag: 1 = sí descuenta stock al vender)
  │
  └──< detalle_ventas.venta_id (ON DELETE CASCADE)
```

### Tabla: `insumos`

| Columna        | Tipo    | Restricciones                     | Descripción                        |
|----------------|---------|-----------------------------------|------------------------------------|
| `id`           | INTEGER | PK AUTOINCREMENT                  |                                    |
| `nombre`       | TEXT    | NOT NULL UNIQUE                   | Nombre descriptivo del insumo      |
| `unidad`       | TEXT    | NOT NULL                          | kg, L, unidades, etc.              |
| `stock`        | REAL    | NOT NULL DEFAULT 0                | Cantidad disponible actual         |
| `stock_minimo` | REAL    | NOT NULL DEFAULT 0                | Umbral de alerta                   |
| `precio_unit`  | REAL    | NOT NULL DEFAULT 0                | Precio de compra por unidad        |
| `created_at`   | TEXT    | NOT NULL DEFAULT (datetime('now'))| ISO-8601                           |
| `updated_at`   | TEXT    | NOT NULL DEFAULT (datetime('now'))| ISO-8601, se actualiza en UPDATE   |

### Tabla: `productos`

| Columna        | Tipo    | Restricciones                     | Descripción                      |
|----------------|---------|-----------------------------------|----------------------------------|
| `id`           | INTEGER | PK AUTOINCREMENT                  |                                  |
| `nombre`       | TEXT    | NOT NULL UNIQUE                   |                                  |
| `categoria`    | TEXT    | NOT NULL                          | Ej: "Hamburguesas", "Bebidas"    |
| `precio_venta` | REAL    | NOT NULL                          |                                  |
| `activo`       | INTEGER | NOT NULL DEFAULT 1                | Soft delete: 0 = desactivado     |
| `created_at`   | TEXT    | NOT NULL DEFAULT (datetime('now'))| ISO-8601                         |

### Tabla: `recetas`

| Columna              | Tipo    | Restricciones                        | Descripción                           |
|----------------------|---------|--------------------------------------|---------------------------------------|
| `id`                 | INTEGER | PK AUTOINCREMENT                     |                                       |
| `producto_id`        | INTEGER | FK → productos(id) ON DELETE CASCADE | Borra receta si se borra el producto  |
| `insumo_id`          | INTEGER | FK → insumos(id) ON DELETE RESTRICT  | No se puede borrar insumo con recetas |
| `cantidad_requerida` | REAL    | NOT NULL                             | Cantidad por unidad de producto       |
| —                    | —       | UNIQUE(producto_id, insumo_id)       | Sin duplicados por combinación        |

### Tabla: `ventas`

| Columna             | Tipo    | Restricciones                     | Descripción                           |
|---------------------|---------|-----------------------------------|---------------------------------------|
| `id`                | INTEGER | PK AUTOINCREMENT                  |                                       |
| `fecha`             | TEXT    | NOT NULL DEFAULT (datetime('now'))| ISO-8601                              |
| `total`             | REAL    | NOT NULL                          | Suma total de la venta                |
| `metodo_pago`       | TEXT    | NOT NULL DEFAULT 'efectivo'       | efectivo / tarjeta / transferencia    |
| `descontar_insumos` | INTEGER | NOT NULL DEFAULT 1                | Flag: si 1, descuenta stock al vender |

### Tabla: `detalle_ventas`

| Columna           | Tipo    | Restricciones                         | Descripción                      |
|-------------------|---------|---------------------------------------|----------------------------------|
| `id`              | INTEGER | PK AUTOINCREMENT                      |                                  |
| `venta_id`        | INTEGER | FK → ventas(id) ON DELETE CASCADE     | Borra detalles si se borra venta |
| `producto_id`     | INTEGER | FK → productos(id) ON DELETE RESTRICT | No borrar producto con ventas    |
| `cantidad`        | INTEGER | NOT NULL DEFAULT 1                    |                                  |
| `precio_unitario` | REAL    | NOT NULL                              | Precio al momento de la venta    |

### Tabla: `compras`

| Columna       | Tipo    | Restricciones                       | Descripción              |
|---------------|---------|-------------------------------------|--------------------------|
| `id`          | INTEGER | PK AUTOINCREMENT                    |                          |
| `insumo_id`   | INTEGER | FK → insumos(id) ON DELETE RESTRICT | No borrar con compras    |
| `cantidad`    | REAL    | NOT NULL                            | Cantidad adquirida       |
| `costo_total` | REAL    | NOT NULL                            | Costo total de la compra |
| `fecha`       | TEXT    | NOT NULL DEFAULT (datetime('now'))  | ISO-8601                 |
| `proveedor`   | TEXT    | —                                   | Opcional                 |

### Índices

| Índice                    | Tabla          | Columna     | Propósito                           |
|---------------------------|----------------|-------------|-------------------------------------|
| `idx_ventas_fecha`        | ventas         | fecha       | Reportes por rango de fechas        |
| `idx_compras_fecha`       | compras        | fecha       | Reportes por rango de fechas        |
| `idx_detalle_venta_id`    | detalle_ventas | venta_id    | JOIN rápido al listar detalle       |
| `idx_recetas_producto_id` | recetas        | producto_id | JOIN al calcular insumos necesarios |

### Script completo (`database/schema.py`)

```python
SQL_SCHEMA = """
CREATE TABLE IF NOT EXISTS insumos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT    NOT NULL UNIQUE,
    unidad          TEXT    NOT NULL,
    stock           REAL    NOT NULL DEFAULT 0,
    stock_minimo    REAL    NOT NULL DEFAULT 0,
    precio_unit     REAL    NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS productos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT    NOT NULL UNIQUE,
    categoria       TEXT    NOT NULL,
    precio_venta    REAL    NOT NULL,
    activo          INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS recetas (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id         INTEGER NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    insumo_id           INTEGER NOT NULL REFERENCES insumos(id)   ON DELETE RESTRICT,
    cantidad_requerida  REAL    NOT NULL,
    UNIQUE (producto_id, insumo_id)
);

CREATE TABLE IF NOT EXISTS ventas (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha               TEXT    NOT NULL DEFAULT (datetime('now')),
    total               REAL    NOT NULL,
    metodo_pago         TEXT    NOT NULL DEFAULT 'efectivo',
    descontar_insumos   INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS detalle_ventas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id        INTEGER NOT NULL REFERENCES ventas(id)    ON DELETE CASCADE,
    producto_id     INTEGER NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
    cantidad        INTEGER NOT NULL DEFAULT 1,
    precio_unitario REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS compras (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    insumo_id   INTEGER NOT NULL REFERENCES insumos(id) ON DELETE RESTRICT,
    cantidad    REAL    NOT NULL,
    costo_total REAL    NOT NULL,
    fecha       TEXT    NOT NULL DEFAULT (datetime('now')),
    proveedor   TEXT
);

CREATE INDEX IF NOT EXISTS idx_ventas_fecha        ON ventas(fecha);
CREATE INDEX IF NOT EXISTS idx_compras_fecha       ON compras(fecha);
CREATE INDEX IF NOT EXISTS idx_detalle_venta_id    ON detalle_ventas(venta_id);
CREATE INDEX IF NOT EXISTS idx_recetas_producto_id ON recetas(producto_id);
"""
```

> ⚠️ **Sin cambios al schema en ninguna sesión.** El schema original se mantiene intacto.
> Si en futuras sesiones se requiere una migración, se documentará aquí con fecha y motivo.
