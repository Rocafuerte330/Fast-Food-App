# database/schema.py

SQL_SCHEMA = """
-- database/schema.py  (ejecutar una sola vez al iniciar la app)

CREATE TABLE IF NOT EXISTS insumos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT    NOT NULL UNIQUE,
    unidad_medida   TEXT    NOT NULL,          -- 'kg', 'litros', 'unidades', etc.
    cantidad_stock  REAL    NOT NULL DEFAULT 0,
    costo_unitario  REAL    NOT NULL DEFAULT 0, -- costo por unidad de medida
    stock_minimo    REAL    NOT NULL DEFAULT 0, -- para alertas de bajo stock
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS productos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT    NOT NULL UNIQUE,
    categoria       TEXT    NOT NULL,          -- 'plato', 'bebida', 'combo'
    precio_venta    REAL    NOT NULL,
    activo          INTEGER NOT NULL DEFAULT 1, -- 0 = oculto del menú
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Tabla puente: define cuánto insumo consume cada plato
CREATE TABLE IF NOT EXISTS recetas (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id         INTEGER NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    insumo_id           INTEGER NOT NULL REFERENCES insumos(id)   ON DELETE RESTRICT,
    cantidad_requerida  REAL    NOT NULL,       -- en la misma unidad que insumos.unidad_medida
    UNIQUE (producto_id, insumo_id)
);

-- Cabecera de venta (una transacción completa)
CREATE TABLE IF NOT EXISTS ventas (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha               TEXT    NOT NULL DEFAULT (datetime('now')),
    total               REAL    NOT NULL,
    metodo_pago         TEXT    NOT NULL DEFAULT 'efectivo',
    descontar_insumos   INTEGER NOT NULL DEFAULT 1  -- 1 = sí descontar stock
);

-- Líneas de cada venta (qué productos y cuántos)
CREATE TABLE IF NOT EXISTS detalle_ventas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id        INTEGER NOT NULL REFERENCES ventas(id)   ON DELETE CASCADE,
    producto_id     INTEGER NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
    cantidad        INTEGER NOT NULL DEFAULT 1,
    precio_unitario REAL    NOT NULL                          -- precio histórico al momento de venta
);

-- Registro de compras de insumos (genera los GASTOS en contabilidad)
CREATE TABLE IF NOT EXISTS compras (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    insumo_id   INTEGER NOT NULL REFERENCES insumos(id) ON DELETE RESTRICT,
    cantidad    REAL    NOT NULL,
    costo_total REAL    NOT NULL,
    fecha       TEXT    NOT NULL DEFAULT (datetime('now')),
    proveedor   TEXT
);

-- Índices para acelerar los reportes más comunes
CREATE INDEX IF NOT EXISTS idx_ventas_fecha        ON ventas(fecha);
CREATE INDEX IF NOT EXISTS idx_compras_fecha       ON compras(fecha);
CREATE INDEX IF NOT EXISTS idx_detalle_venta_id    ON detalle_ventas(venta_id);
CREATE INDEX IF NOT EXISTS idx_recetas_producto_id ON recetas(producto_id);
"""