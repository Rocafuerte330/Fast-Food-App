## 🧾 Estado del Proyecto — Fast Food App

**Sesión:** #1  |  **Fecha:** 2026-Mayo-06
**Colaboradora:** [Wendy Ortega] vía Git — rama activa: `feature/...`

---

### Stack
- GUI: CustomTkinter | DB: SQLite | Reportes: openpyxl + reportlab
- Python: 3.11+ | Entorno: venv (`/venv`)

### Módulos — estado actual
| Módulo            | Estado            | Notas rápidas                     |
|-------------------|-------------------|-----------------------------------|
| `database/`       | ✅ Completo       | schema.py + conexión singleton    |
| `models/`         | ✅ Completo       | dataclasses definidas             |
| `services/inventory` | 🔄 En progreso | CRUD listo, falta alerta de stock |
| `services/sales`  | ⏳ Pendiente      | lógica de descuento sin empezar   |
| `services/accounting` | ⏳ Pendiente  |                                   |
| `ui/inventory_view`  | ⏳ Pendiente   |                                   |
| `ui/sales_view`   | ⏳ Pendiente      |                                   |
| `ui/accounting_view` | ⏳ Pendiente  |                                   |

### Última tarea completada
> [Describir brevemente qué se terminó en la sesión anterior]

### Bloqueantes / decisiones pendientes
1. [Ej: ¿Cómo manejar ventas sin receta configurada?]
2. ...

### Próximo objetivo de esta sesión
> [Una sola tarea concreta. Ej: "Implementar `sales_service.py` con descuento de insumos"]

### Convenciones acordadas
- Todos los repositorios reciben un `db_connection` por inyección (no lo crean internamente)
- Fechas en ISO-8601: `datetime('now')` de SQLite
- Los servicios no hacen `print()` — lanzan excepciones que la UI captura