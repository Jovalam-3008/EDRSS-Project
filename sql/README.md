# Secuencia SQL de EDRSS V2

| Orden | Carpeta | Responsabilidad |
|---:|---|---|
| 00 | `00_setup` | Esquemas y funciones comunes |
| 01 | `01_bronze` | Tablas de ingesta y datos fuente |
| 02 | `02_silver` | Limpieza, reglas de calidad y features determinísticas |
| 03 | `03_gold` | Contratos para entrenamiento, scoring y KPIs |
| 04 | `04_model` | Vistas para consultar el modelo activo |
| 05 | `05_dashboard` | Marts y vistas de cada página del tablero |
| 06 | `06_quality` | Controles finales y observabilidad |

## Criterio de diseño

- Un script resuelve una responsabilidad principal.
- Los nombres indican el orden y el resultado.
- La ejecución es idempotente cuando PostgreSQL lo permite.
- Las transformaciones no se duplican en Python ni en los notebooks.
- Los dashboards nunca consultan Bronze o Silver.

