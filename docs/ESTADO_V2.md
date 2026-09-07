# Estado de implementación EDRSS V2

Fecha de validación: 6 de septiembre de 2026, zona horaria America/Lima.

## Plataforma de datos

- Conexión al nuevo proyecto Supabase: aprobada.
- Scripts SQL desplegados en orden: 9.
- Lote activo: `551e4f69-91d3-4426-aff4-761f0467c770`.
- Bronze: 209,593 filas.
- Silver: 209,593 filas.
- Gold: 209,593 filas.
- `gold.ml_training`: 150,768 filas.
- `gold.ml_scoring`: 58,825 filas.

## Modelo productivo

- Modelo activo: Random Forest.
- Versión: `edrss-v2-20260907T010913Z`.
- ROC-AUC OOT: 0.8435.
- Average Precision OOT: 0.6010.
- Recall OOT al umbral operativo: 0.7320.
- Precisión OOT al umbral operativo: 0.4881.
- Predicciones publicadas: 164,034.

## Capacidad de cobranza OOT

| Capacidad | Contactos | Morosos capturados | Precisión | Recall | Lift |
|---:|---:|---:|---:|---:|---:|
| 5% | 1,581 | 1,229 | 77.74% | 18.82% | 3.76x |
| 10% | 3,161 | 2,198 | 69.54% | 33.67% | 3.37x |
| 20% | 6,321 | 3,716 | 58.79% | 56.92% | 2.85x |

## Consumibles del dashboard

| Hoja | Vista | Filas validadas |
|---|---|---:|
| Resumen ejecutivo | `api.page_executive_summary` | 1 |
| Riesgo y mora | `api.page_risk_and_delinquency` | 82 |
| Comportamiento | `api.page_customer_behavior` | 106 |
| Modelo predictivo | `api.page_predictive_model` | 42 |
| Priorización | `api.page_collection_priority` | 58,825 |
| Calidad | `api.page_data_quality` | 6 |

## Entregables académicos

- Informe Word V2 con 15 páginas, estructura institucional, resultados, gobierno y anexos.
- Presentación de defensa con 14 diapositivas y tres gráficos editables.

## Próxima fase

Preparar la simulación de defensa, asignar intervenciones por integrante y ensayar respuestas a preguntas técnicas y de negocio.
