# Arquitectura EDRSS V2

## Objetivo

EDRSS V2 convierte la fuente de microcréditos móviles en una cola priorizada de cobranza temprana. La solución mantiene una secuencia explícita y evita duplicar transformaciones entre SQL, Python y notebooks.

## Flujo

```text
dataset.csv
    │
    ▼
Bronze · copia fiel y lote de ingesta
    │
    ▼
Silver · tipos, reglas, anomalías y features determinísticas
    │
    ▼
Gold · ml_training, ml_scoring, KPIs y resultados del modelo
    │
    ▼
API · una vista controlada por hoja del dashboard
    │
    ├── Resumen ejecutivo
    ├── Riesgo y mora
    ├── Comportamiento
    ├── Modelo predictivo
    ├── Priorización
    └── Calidad de datos
```

## Responsabilidad por tecnología

| Tecnología | Responsabilidad |
|---|---|
| SQL | Transformar y certificar datos |
| Python | Conexión, ingesta, entrenamiento y publicación |
| Notebooks | Explicar, ejecutar y validar la secuencia |
| Streamlit | Presentar e interactuar con consumibles Gold/API |

## Controles contra leakage

- El TARGET se madura hasta el 23 de julio de 2016.
- TRAIN termina el 7 de julio.
- Existe un embargo entre el 8 y el 12 de julio.
- OOT comprende del 13 al 23 de julio.
- La población posterior se reserva para scoring.
- `payback30` y `payback90` no forman parte del contrato predictivo publicado.

## Seguridad

La configuración versionada contiene únicamente host, puerto, base y usuario. La contraseña se solicita con entrada oculta y no se escribe en archivos, notebooks, modelos ni salidas.

