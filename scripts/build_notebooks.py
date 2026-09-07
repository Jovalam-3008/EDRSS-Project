"""Genera los notebooks V2 con una estructura uniforme y fácil de revisar."""

from pathlib import Path

import nbformat as nbf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = PROJECT_ROOT / "notebooks"


BOOTSTRAP = """from pathlib import Path
import sys

PROJECT_ROOT = Path.cwd().resolve()
if PROJECT_ROOT.name.lower() in {"notebooks", "executed"}:
    PROJECT_ROOT = PROJECT_ROOT.parent if PROJECT_ROOT.name.lower() == "notebooks" else PROJECT_ROOT.parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
print(f"Proyecto: {PROJECT_ROOT.name}")"""


def markdown(text: str):
    return nbf.v4.new_markdown_cell(text)


def code(text: str):
    return nbf.v4.new_code_cell(text)


def notebook(title: str, purpose: str, cells: list) -> nbf.NotebookNode:
    book = nbf.v4.new_notebook()
    book["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3"},
    }
    book["cells"] = [
        markdown(f"# {title}\n\n**Objetivo:** {purpose}\n\nEste notebook es parte del flujo secuencial EDRSS V2."),
        markdown("## 1. Preparación\n\nUbicamos la raíz del proyecto e importamos únicamente las funciones necesarias."),
        code(BOOTSTRAP),
        *cells,
    ]
    return book


BOOKS = {
    "00_Configuracion_y_conexion.ipynb": notebook(
        "00 · Configuración y conexión",
        "comprobar el entorno, la fuente y la conexión segura con Supabase.",
        [
            markdown("## 2. Validación local\n\nLa contraseña no participa en esta comprobación."),
            code("from src.settings import load_settings\nfrom src.pipeline import validate_source\n\nsettings = load_settings()\nprint(settings)\nvalidate_source()"),
            markdown("## 3. Conexión e inventario\n\nLa contraseña se solicita oculta y permanece solo durante este kernel."),
            code("from src.database import inventory, test_connection\n\ntest_connection(), inventory()"),
            markdown("## Resultado esperado\n\nConexión confirmada y fuente con 35 columnas. Continúe con el notebook 01."),
        ],
    ),
    "01_Ingesta_Bronze.ipynb": notebook(
        "01 · Ingesta Bronze",
        "cargar una copia fiel y trazable del CSV sin reglas de negocio.",
        [
            markdown("## 2. Validar la fuente"),
            code("from src.pipeline import ingest_bronze, validate_source\n\nvalidate_source()"),
            markdown("## 3. Ingestar o reutilizar el lote\n\nLa huella MD5 evita duplicar la misma fuente."),
            code("ingestion = ingest_bronze()\ningestion"),
            markdown("## 4. Validar Bronze"),
            code("from src.database import query_dataframe\n\nquery_dataframe('''\nselect batch_id, source_file_name, loaded_row_count, status, completed_at\nfrom bronze.ingestion_batch order by started_at desc limit 5\n''')"),
            markdown("## Resultado esperado\n\n209,593 filas cargadas o un lote anterior reutilizado. Continúe con el notebook 02."),
        ],
    ),
    "02_Limpieza_Silver.ipynb": notebook(
        "02 · Limpieza Silver",
        "tipificar la fuente, aplicar reglas de calidad y construir features determinísticas.",
        [
            markdown("## 2. Ejecutar limpieza y features Silver"),
            code("from src.pipeline import latest_successful_batch, refresh_silver\n\nbatch_id = latest_successful_batch()\nrefresh_silver(batch_id)\nbatch_id"),
            markdown("## 3. Revisar calidad\n\nLos registros no se borran silenciosamente: las anomalías se marcan y se auditan."),
            code("from src.database import query_dataframe\n\nquery_dataframe('''\nselect layer_name, check_name, status, observed_value, expected_value\nfrom silver.data_quality_result\nwhere batch_id = %s\norder by checked_at, check_name\n''', (batch_id,))"),
            markdown("## Resultado esperado\n\nSilver conserva la trazabilidad de Bronze y separa la madurez temporal. Continúe con el notebook 03."),
        ],
    ),
    "03_Construccion_Gold.ipynb": notebook(
        "03 · Construcción Gold",
        "publicar contratos certificados para entrenamiento, scoring y consumo analítico.",
        [
            markdown("## 2. Promover el lote a Gold"),
            code("from src.pipeline import latest_successful_batch, refresh_gold, layer_counts\n\nbatch_id = latest_successful_batch()\nrefresh_gold(batch_id)\nlayer_counts(batch_id)"),
            markdown("## 3. Verificar particiones temporales"),
            code("from src.database import query_dataframe\n\nquery_dataframe('''\nselect dataset_role, target_maturity_status, count(*) as rows, avg(riesgo_mora) as delinquency_rate\nfrom gold.ml_features\nwhere batch_id = %s\ngroup by dataset_role, target_maturity_status\norder by dataset_role\n''', (batch_id,))"),
            markdown("## Resultado esperado\n\n`gold.ml_training` y `gold.ml_scoring` quedan listos. Continúe con el notebook 04."),
        ],
    ),
    "04_EDA_y_KPIs_de_negocio.ipynb": notebook(
        "04 · EDA y KPIs de negocio",
        "explicar el problema de mora antes de entrenar un modelo.",
        [
            markdown("## 2. Cargar únicamente Gold"),
            code("import matplotlib.pyplot as plt\nimport seaborn as sns\nfrom src.database import query_dataframe\n\ndaily = query_dataframe('select * from api.page_risk_and_delinquency order by pdate')\ndaily.head()"),
            markdown("## 3. Evolución temporal del riesgo"),
            code("plot_data = daily.dropna(subset=['delinquency_rate']).copy()\nplt.figure(figsize=(12, 4))\nsns.lineplot(data=plot_data, x='pdate', y='delinquency_rate', hue='dataset_role', marker='o')\nplt.title('Evolución temporal de la mora')\nplt.ylabel('Tasa de mora')\nplt.xlabel('Fecha')\nplt.xticks(rotation=45)\nplt.tight_layout();"),
            markdown("## 4. Perfil de comportamiento"),
            code("behavior = query_dataframe('select * from api.page_customer_behavior')\nbehavior.groupby('riesgo_mora').agg(operations=('operations','sum'), avg_recharge=('avg_recharge_amount_30d','mean'), avg_loan=('avg_loan_amount_30d','mean'))"),
            markdown("## Conclusión\n\nDocumente los hallazgos que justifican la priorización y continúe con el notebook 05."),
        ],
    ),
    "05_Modelo_predictivo.ipynb": notebook(
        "05 · Modelo predictivo",
        "comparar tres candidatos con validación temporal y congelar un candidato reproducible.",
        [
            markdown("## 2. Entrenar y evaluar\n\nEl preprocesamiento se ajusta dentro de cada fold. OOT no participa en la selección."),
            code("from src.modeling import train_and_evaluate\n\nresult = train_and_evaluate()\nresult['cv_summary']"),
            markdown("## 3. Revisar OOF y OOT"),
            code("print('Modelo:', result['selected_model_name'])\nprint('OOF:', result['oof_metrics'])\nprint('OOT:', result['oot_metrics'])\nresult['oot_capacity']"),
            markdown("## 4. Guardar candidato para publicación"),
            code("import joblib\n\ncandidate_path = PROJECT_ROOT / 'outputs' / 'model_candidate.joblib'\njoblib.dump(result, candidate_path)\nprint(candidate_path)"),
            markdown("## Resultado esperado\n\nUn candidato evaluado y congelado. El notebook 06 realiza la publicación controlada."),
        ],
    ),
    "06_Publicacion_de_scoring.ipynb": notebook(
        "06 · Publicación de scoring",
        "registrar el modelo aprobado, publicar scores y construir la cola de cobranza.",
        [
            markdown("## 2. Recuperar el candidato evaluado"),
            code("import joblib\nfrom src.modeling import publish_model, published_model_summary\n\ncandidate_path = PROJECT_ROOT / 'outputs' / 'model_candidate.joblib'\nresult = joblib.load(candidate_path)"),
            markdown("## 3. Publicar el modelo y las predicciones"),
            code("publication = publish_model(result)\npublication"),
            markdown("## 4. Confirmar el modelo activo"),
            code("published_model_summary()"),
            markdown("## Resultado esperado\n\nModelo activo, métricas, scores y prioridad disponibles en Gold/API. Continúe con el notebook 07."),
        ],
    ),
    "07_Validacion_del_dashboard.ipynb": notebook(
        "07 · Validación del dashboard",
        "conciliar los indicadores de cada hoja con los consumibles certificados.",
        [
            markdown("## 2. Resumen ejecutivo"),
            code("from src.database import query_dataframe\n\nexecutive = query_dataframe('select * from api.page_executive_summary')\nexecutive"),
            markdown("## 3. Volumen de consumibles por hoja"),
            code("views = ['page_risk_and_delinquency','page_customer_behavior','page_predictive_model','page_collection_priority','page_data_quality']\nchecks = []\nfor view in views:\n    rows = query_dataframe(f'select count(*) as rows from api.{view}').iloc[0, 0]\n    checks.append({'view': view, 'rows': int(rows)})\nchecks"),
            markdown("## 4. Arranque del tablero\n\nDesde una terminal en la raíz ejecute: `streamlit run dashboard/app.py`."),
            markdown("## Resultado final\n\nTodos los KPIs del tablero provienen de Gold/API y pueden conciliarse con SQL."),
        ],
    ),
}


def main() -> None:
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    for filename, book in BOOKS.items():
        nbf.write(book, NOTEBOOK_DIR / filename)
        print("OK", filename)


if __name__ == "__main__":
    main()

