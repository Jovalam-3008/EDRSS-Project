# Early Delinquency Risk Scoring System — V2

EDRSS V2 organiza el proyecto de cobranza temprana con arquitectura Medallion y una ejecución lineal. La V1 permanece intacta como respaldo.

## Enlaces públicos

- [Dashboard en Streamlit](https://edrss-dashboard-hjcbxwakvf6js8yn6evnhe.streamlit.app/)
- [Repositorio independiente del dashboard](https://github.com/Jovalam-3008/EDRSS-Dashboard)
- [Repositorio completo del proyecto](https://github.com/Jovalam-3008/EDRSS-Project)

## Principios

1. SQL transforma los datos.
2. Python gestiona conexión, ingesta, modelamiento y scoring.
3. Los notebooks ejecutan, explican y validan cada etapa.
4. El dashboard consume únicamente vistas certificadas de Gold/API.
5. Ninguna contraseña se guarda en archivos o notebooks.

## Orden de ejecución

1. `00_Configuracion_y_conexion.ipynb`
2. `01_Ingesta_Bronze.ipynb`
3. `02_Limpieza_Silver.ipynb`
4. `03_Construccion_Gold.ipynb`
5. `04_EDA_y_KPIs_de_negocio.ipynb`
6. `05_Modelo_predictivo.ipynb`
7. `06_Publicacion_de_scoring.ipynb`
8. `07_Validacion_del_dashboard.ipynb`

## Capas

- **Bronze:** copia trazable del CSV.
- **Silver:** tipificación, limpieza, cuarentena y variables determinísticas.
- **Gold:** contratos de entrenamiento, scoring, KPIs y marts de dashboard.
- **API:** exposición controlada de los consumibles Gold.

## Inicio rápido

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\deploy_sql.py
```

La contraseña de Supabase se solicita de forma oculta y solo permanece en memoria durante el proceso.

Para iniciar el tablero multipágina:

```powershell
.\.venv\Scripts\streamlit.exe run dashboard\app.py
```

Para iniciar la demo pública sin credenciales ni operaciones individuales:

```powershell
.\.venv\Scripts\python.exe scripts\build_public_dashboard_snapshot.py
.\.venv\Scripts\streamlit.exe run dashboard\public_app.py
```

En Streamlit Community Cloud, el archivo principal es `dashboard/public_app.py`.

## Entregables académicos

- `deliverables/Informe_EDRSS_V2.docx`
- `deliverables/Presentacion_Defensa_EDRSS_V2_Final.pptx`

## Convención SQL

Los scripts se ejecutan por ruta y número. Cada archivo declara objetivo, entradas, salidas, granularidad y validaciones. Consulte `sql/README.md`.
