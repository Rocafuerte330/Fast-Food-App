# 🧾 Estado del Proyecto — Fast Food App

**Sesión:** #2  |  **Fecha:** 2026-05-06
**Colaboradora:** [Wendy Ortega] vía Git — rama activa: `main`

---

### Stack
- GUI: CustomTkinter | DB: SQLite | Reportes: openpyxl + reportlab
- Python: 3.11+ | Entorno: venv (`/venv`) | Sistema de desarrollo: macOS ✅

### Módulos — estado actual

| Módulo                    | Estado            | Notas rápidas                                        |
|---------------------------|-------------------|------------------------------------------------------|
| `database/schema.py`      | ✅ Completo       | SQL_SCHEMA con 6 tablas + índices definidos          |
| `database/connection.py`  | ✅ Completo       | Singleton, row_factory, PRAGMA foreign_keys ON       |
| `database/__init__.py`    | ✅ Completo       | Archivo de paquete creado                            |
| `models/`                 | ⏳ Pendiente      | Dataclasses por definir                              |
| `services/inventory`      | ⏳ Pendiente      |                                                      |
| `services/sales`          | ⏳ Pendiente      | Lógica de descuento de insumos sin empezar           |
| `services/accounting`     | ⏳ Pendiente      |                                                      |
| `services/report`         | ⏳ Pendiente      | Excel / PDF                                          |
| `ui/app.py` (`main.py`)   | ✅ Completo       | Ventana CTk base + botón Test DB funcional           |
| `ui/inventory_view.py`    | ⏳ Pendiente      |                                                      |
| `ui/sales_view.py`        | ⏳ Pendiente      |                                                      |
| `ui/accounting_view.py`   | ⏳ Pendiente      |                                                      |

### Última tarea completada — Sesión #2
> Fase 1 (Cimientos) completada. Se implementaron `database/schema.py`, `database/connection.py` y `main.py`. La conexión a SQLite fue probada exitosamente en macOS: el botón "Test DB" confirmó la creación de las 6 tablas (`compras`, `detalle_ventas`, `insumos`, `productos`, `recetas`, `ventas`). El archivo `.db` se genera automáticamente en la primera ejecución.

### Bloqueantes / decisiones pendientes
1. Definir si los `models/` serán `@dataclass` o `TypedDict` (impacta cómo los repositorios devuelven datos).
2. ¿Se necesita autenticación de usuario (contraseña de acceso) para la app?

### Próximo objetivo — Sesión #3
> Implementar `models/` (dataclasses para `Insumo`, `Producto`, `Venta`) y el repositorio `database/repositories/insumo_repository.py` con operaciones CRUD completas.

### Convenciones acordadas
- Todos los repositorios reciben `db_connection` por inyección (no lo crean internamente)
- Fechas en ISO-8601: `datetime('now')` de SQLite
- Los servicios no hacen `print()` — lanzan excepciones que la UI captura
- `row_factory = sqlite3.Row` activo: acceso a columnas por nombre (`fila["nombre"]`)
- Punto de entrada siempre desde la raíz: `python main.py`

### Fases del proyecto

| Fase | Nombre        | Estado         |
|------|---------------|----------------|
| 1    | Cimientos     | ✅ Completada  |
| 2    | Inventario    | 🔄 Siguiente   |
| 3    | Ventas        | ⏳ Pendiente   |
| 4    | Reportes      | ⏳ Pendiente   |