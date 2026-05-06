# database/schema.py

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