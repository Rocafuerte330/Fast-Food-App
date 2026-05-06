# 🧾 Estado del Proyecto — Fast Food App

**Sesión:** #3  |  **Fecha:** 2026-05-06
**Colaboradora:** [Wendy Ortega] vía Git — rama activa: `main`

---

### Stack
- GUI: CustomTkinter | DB: SQLite | Reportes: openpyxl + reportlab
- Python: 3.11+ | Entorno: venv (`/venv`) | SO probado: macOS ✅

---

### Módulos — estado actual

| Módulo                                          | Estado       | Notas rápidas                                        |
|-------------------------------------------------|--------------|------------------------------------------------------|
| `database/schema.py`                            | ✅ Completo  | SQL_SCHEMA con 6 tablas + índices                    |
| `database/connection.py`                        | ✅ Completo  | Singleton, row_factory, PRAGMA foreign_keys ON       |
| `database/repositories/insumo_repository.py`    | ✅ Completo  | CRUD + actualizar_stock + listar_bajo_stock          |
| `models/insumo.py`                              | ✅ Completo  | @dataclass, bajo_stock, valor_total, from_row()      |
| `models/` (resto)                               | ⏳ Pendiente | Producto, Receta, Venta, etc. — siguiente fase       |
| `services/inventory_service.py`                 | ⏳ Pendiente | Alerta de stock mínimo (base ya lista en repo)       |
| `services/sales`                                | ⏳ Pendiente | Incluirá lógica de descuento automático de insumos   |
| `services/accounting`                           | ⏳ Pendiente |                                                      |
| `services/report`                               | ⏳ Pendiente | Excel (openpyxl) + PDF (reportlab)                   |
| `ui/inventory_view.py`                          | ✅ Completo  | Tabla con scroll, banner alertas, modal CRUD         |
| `ui/sales_view.py`                              | ⏳ Pendiente |                                                      |
| `ui/accounting_view.py`                         | ⏳ Pendiente |                                                      |
| `main.py`                                       | ✅ Completo  | Ventana CTk base + botón Test DB funcionando         |

---

### Última tarea completada

> **Fase 2 — Módulo de Inventario (Sesión #3):** Se implementaron `models/insumo.py`,
> `database/repositories/insumo_repository.py` y `ui/inventory_view.py`.
> El repositorio cubre CRUD completo + ajuste de stock por delta (positivo/negativo)
> listo para integrarse con ventas y compras. La vista incluye tabla con scroll,
> banner de alertas de bajo stock, selección por clic y diálogo modal reutilizable
> para crear y editar insumos.
> ✅ Probado exitosamente en macOS. Los 3 módulos funcionan sin errores.

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

---

### Bloqueantes / decisiones pendientes

1. ~~Definir si `models/` usará `dataclasses` estándar o con validación adicional.~~ → **Resuelto:** `@dataclass` estándar de Python.
2. Decidir pantalla de inicio: ¿menú lateral fijo o navegación por tabs?

---

### Próximo objetivo

> **Fase 3 — Módulo de Productos y Recetas:** Implementar `models/producto.py`,
> `models/receta.py`, sus repositorios y la vista `ui/products_view.py`.
> También definir `services/inventory_service.py` con la lógica de alerta de stock mínimo
> desacoplada de la UI.

---

### Convenciones acordadas

- Los repositorios reciben `db_connection` por inyección (no la crean internamente).
- Fechas en ISO-8601: `datetime.now().isoformat()` en Python / `datetime('now')` en SQLite.
- Los servicios no usan `print()` — lanzan excepciones que la UI captura.
- `row_factory = sqlite3.Row` activo: acceso a columnas por nombre.
- Archivo `.db` en `.gitignore` — no se versiona.
- `@dataclass` estándar para todos los modelos (sin librerías de validación externas).
- `actualizar_stock(id, delta)` acepta positivo (entrada) y negativo (salida) — patrón para ventas y compras.

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
  │ descontar_insumos (flag: 1=sí descuenta stock)
  │
  └──< detalle_ventas.venta_id (ON DELETE CASCADE)
```

### Tabla: `insumos`

| Columna        | Tipo    | Restricciones                    | Descripción                        |
|----------------|---------|----------------------------------|------------------------------------|
| `id`           | INTEGER | PK AUTOINCREMENT                 |                                    |
| `nombre`       | TEXT    | NOT NULL UNIQUE                  | Nombre descriptivo del insumo      |
| `unidad`       | TEXT    | NOT NULL                         | kg, L, unidades, etc.              |
| `stock`        | REAL    | NOT NULL DEFAULT 0               | Cantidad disponible actual         |
| `stock_minimo` | REAL    | NOT NULL DEFAULT 0               | Umbral de alerta                   |
| `precio_unit`  | REAL    | NOT NULL DEFAULT 0               | Precio de compra por unidad        |
| `created_at`   | TEXT    | NOT NULL DEFAULT (datetime('now'))| ISO-8601                          |
| `updated_at`   | TEXT    | NOT NULL DEFAULT (datetime('now'))| ISO-8601, se actualiza en UPDATE  |

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

| Columna               | Tipo    | Restricciones                            | Descripción                     |
|-----------------------|---------|------------------------------------------|---------------------------------|
| `id`                  | INTEGER | PK AUTOINCREMENT                         |                                 |
| `producto_id`         | INTEGER | FK → productos(id) ON DELETE CASCADE     | Si se borra el producto, borra la receta |
| `insumo_id`           | INTEGER | FK → insumos(id) ON DELETE RESTRICT      | No se puede borrar insumo con recetas |
| `cantidad_requerida`  | REAL    | NOT NULL                                 | Cantidad por unidad de producto  |
| —                     | —       | UNIQUE(producto_id, insumo_id)           | Sin duplicados por combinación   |

### Tabla: `ventas`

| Columna             | Tipo    | Restricciones                     | Descripción                           |
|---------------------|---------|-----------------------------------|---------------------------------------|
| `id`                | INTEGER | PK AUTOINCREMENT                  |                                       |
| `fecha`             | TEXT    | NOT NULL DEFAULT (datetime('now'))| ISO-8601                              |
| `total`             | REAL    | NOT NULL                          | Suma total de la venta                |
| `metodo_pago`       | TEXT    | NOT NULL DEFAULT 'efectivo'       | efectivo, tarjeta, transferencia, etc.|
| `descontar_insumos` | INTEGER | NOT NULL DEFAULT 1                | Flag: si 1, descuenta stock al vender |

### Tabla: `detalle_ventas`

| Columna          | Tipo    | Restricciones                           | Descripción                    |
|------------------|---------|-----------------------------------------|--------------------------------|
| `id`             | INTEGER | PK AUTOINCREMENT                        |                                |
| `venta_id`       | INTEGER | FK → ventas(id) ON DELETE CASCADE       | Borra detalles si se borra venta |
| `producto_id`    | INTEGER | FK → productos(id) ON DELETE RESTRICT   | No borrar producto con ventas  |
| `cantidad`       | INTEGER | NOT NULL DEFAULT 1                      |                                |
| `precio_unitario`| REAL    | NOT NULL                                | Precio al momento de la venta  |

### Tabla: `compras`

| Columna       | Tipo    | Restricciones                           | Descripción                    |
|---------------|---------|-----------------------------------------|--------------------------------|
| `id`          | INTEGER | PK AUTOINCREMENT                        |                                |
| `insumo_id`   | INTEGER | FK → insumos(id) ON DELETE RESTRICT     | No borrar insumo con compras   |
| `cantidad`    | REAL    | NOT NULL                                | Cantidad adquirida             |
| `costo_total` | REAL    | NOT NULL                                | Costo total de la compra       |
| `fecha`       | TEXT    | NOT NULL DEFAULT (datetime('now'))      | ISO-8601                       |
| `proveedor`   | TEXT    | —                                       | Opcional                       |

### Índices

| Índice                       | Tabla           | Columna      | Propósito                          |
|------------------------------|-----------------|--------------|------------------------------------|
| `idx_ventas_fecha`           | ventas          | fecha        | Reportes por rango de fechas       |
| `idx_compras_fecha`          | compras         | fecha        | Reportes por rango de fechas       |
| `idx_detalle_venta_id`       | detalle_ventas  | venta_id     | JOIN rápido al listar detalle      |
| `idx_recetas_producto_id`    | recetas         | producto_id  | JOIN al calcular insumos necesarios|

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

> ⚠️ **Sin cambios al schema en esta sesión.** El schema original se mantiene intacto.
> Si en futuras sesiones se requiere una migración, se documentará aquí con fecha y motivo.