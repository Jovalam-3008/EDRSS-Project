<div style="display:flex; align-items:center; gap:14px; margin-bottom:18px;">
    <img src="https://i.postimg.cc/J7sf3Lq4/Group.png" alt="FUTURA" style="height:70px;"/>
    <div>
        <div style="font-size:22px; font-weight:700; line-height:1.25;">FUTURA, Data y Analítica Avanzada</div>
        <div style="font-size:16px; line-height:1.35;">Caso aplicado — Clasificación binaria</div>
        <div style="font-size:14px; color:#555; line-height:1.35;">Delinquency Telecom Dataset · Caso 22</div>
    </div>
</div>

---

**Incluye enunciado del caso, guía de análisis y criterios de solución.**

# Mora Temprana — Cobranza Telecom

## Resumen Ejecutivo

Dataset **Delinquency Telecom Dataset** con **209,593 filas** y **35 variables de trabajo**. El caso está diseñado para **Clasificación binaria** en un contexto de cobranza temprana, riesgo de mora, telecomunicaciones y recuperación de cartera.

---

## 1. Contexto de Negocio

Este caso permite trabajar un problema accionable: predecir riesgo de mora o bajo repago usando recargas, préstamos, frecuencia transaccional, montos y payback a 30 y 90 días. El dataset reúne señales propias del dominio y permite conectar el análisis exploratorio con una decisión práctica.

**Decisión que se espera soportar:** el equipo debe transformar el análisis en una recomendación concreta para cobranza temprana, riesgo de mora, telecomunicaciones y recuperación de cartera. La entrega debe dejar claro qué se prioriza, qué se predice o qué segmentos se accionan, y qué haría el stakeholder con los resultados.

---

## 2. Objetivo del Proyecto

**Objetivo principal:**
Predecir riesgo de mora o bajo repago usando recargas, préstamos, frecuencia transaccional, montos y payback a 30 y 90 días.

**Objetivos específicos:**
- Auditar calidad de datos, valores atípicos, codificaciones y variables que puedan generar leakage.
- Preparar variables numéricas, categóricas, fechas, texto o geografía según corresponda.
- Construir una solución reproducible de clasificación binaria.
- Interpretar resultados con lenguaje de negocio y recomendaciones accionables.
- Documentar restricciones éticas, operativas y de despliegue.

### 2.1 Instrucciones para el Estudiante

El estudiante debe construir una solución supervisada para anticipar la variable `label`. El trabajo no consiste solo en obtener una métrica alta: debe explicar qué decisión tomaría el negocio con el score, qué errores son más costosos y cómo se elegiría un umbral de uso.

**Preguntas que debe responder el trabajo:**
- ¿Qué representa la clase positiva de `label` y por qué es relevante para el negocio?
- ¿Qué variables deben excluirse por ser identificadores, leakage o información no disponible al momento de decidir?
- ¿Qué modelo se recomienda y contra qué alternativas fue comparado?
- ¿Qué umbral operativo se usaría y qué costo tiene equivocarse en cada tipo de error?
- ¿Qué acción concreta debe tomar el stakeholder con los clientes, registros o eventos de mayor riesgo?

**No se acepta:** entregar solo accuracy, entrenar con identificadores, reportar métricas sin matriz de confusión, o recomendar acciones sin conectar el modelo con el proceso operativo.

---

## 3. Stakeholders y Audiencia

| Stakeholder | Rol | Interés principal |
|---|---|---|
| Sponsor de negocio | Dueño del problema | Mejorar decisiones, priorización o eficiencia |
| Equipo operativo | Usuario | Aplicar predicciones, segmentos o alertas en procesos reales |
| Analytics / Data Science | Ejecutor | Preparar datos, modelar, validar e interpretar |
| Riesgo / Compliance | Consultado | Revisar sesgos, privacidad, trazabilidad y uso responsable |
| Dirección | Informado | Evaluar impacto, límites y retorno esperado |

---

## 4. Dataset

### 4.1 Descripción General

| Campo | Detalle |
|---|---|
| **Nombre** | Delinquency Telecom Dataset |
| **Fuente** | OpenML |
| **URL** | https://www.openml.org/d/43745 |
| **Licencia** | OpenML / verificar ficha fuente |
| **Filas totales** | 209,593 |
| **Variables** | 35 |
| **Variable objetivo / referencia** | `label` |
| **Tipo de problema** | Clasificación binaria supervisada |
| **Case ID** | 22 |
| **Dataset original** | openml_43745 |
| **Fecha de descarga** | 2026-07-01 |
| **Hash MD5** | `5fc2b932c2cb8a3a09cf4538faf6878a` |

### 4.2 Diccionario de Variables

| Variable | Tipo | Descripción | Comentario |
|---|---|---|---|
| `label` | numérica | TARGET — etiqueta binaria a predecir: label. | Objetivo del modelo |
| `aon` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: aon. | Cobranza / mora |
| `daily_decr30` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: daily decr30. | Cobranza / mora |
| `daily_decr90` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: daily decr90. | Cobranza / mora |
| `rental30` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: rental30. | Cobranza / mora |
| `rental90` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: rental90. | Cobranza / mora |
| `last_rech_date_ma` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: last rech date ma. | Cobranza / mora |
| `last_rech_date_da` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: last rech date da. | Cobranza / mora |
| `last_rech_amt_ma` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: last rech amt ma. | Cobranza / mora |
| `cnt_ma_rech30` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: cnt ma rech30. | Cobranza / mora |
| `fr_ma_rech30` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: fr ma rech30. | Cobranza / mora |
| `sumamnt_ma_rech30` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: sumamnt ma rech30. | Cobranza / mora |
| `medianamnt_ma_rech30` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: medianamnt ma rech30. | Cobranza / mora |
| `medianmarechprebal30` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: medianmarechprebal30. | Cobranza / mora |
| `cnt_ma_rech90` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: cnt ma rech90. | Cobranza / mora |
| `fr_ma_rech90` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: fr ma rech90. | Cobranza / mora |
| `sumamnt_ma_rech90` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: sumamnt ma rech90. | Cobranza / mora |
| `medianamnt_ma_rech90` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: medianamnt ma rech90. | Cobranza / mora |
| `medianmarechprebal90` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: medianmarechprebal90. | Cobranza / mora |
| `cnt_da_rech30` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: cnt da rech30. | Cobranza / mora |
| `fr_da_rech30` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: fr da rech30. | Cobranza / mora |
| `cnt_da_rech90` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: cnt da rech90. | Cobranza / mora |
| `fr_da_rech90` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: fr da rech90. | Cobranza / mora |
| `cnt_loans30` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: cnt loans30. | Cobranza / mora |
| `amnt_loans30` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: amnt loans30. | Cobranza / mora |
| `maxamnt_loans30` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: maxamnt loans30. | Cobranza / mora |
| `medianamnt_loans30` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: medianamnt loans30. | Cobranza / mora |
| `cnt_loans90` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: cnt loans90. | Cobranza / mora |
| `amnt_loans90` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: amnt loans90. | Cobranza / mora |
| `maxamnt_loans90` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: maxamnt loans90. | Cobranza / mora |
| `medianamnt_loans90` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: medianamnt loans90. | Cobranza / mora |
| `payback30` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: payback30. | Cobranza / mora |
| `payback90` | numérica | Indicador de recarga, préstamo, antigüedad o repago para evaluar mora: payback90. | Cobranza / mora |
| `pcircle` | categórica/texto | Campo operativo de producto o fecha usado para contextualizar el registro: pcircle. | Cobranza / mora |
| `pdate` | categórica/texto | Campo operativo de producto o fecha usado para contextualizar el registro: pdate. | Cobranza / mora |

### 4.3 Notas sobre Calidad de Datos

- Revisar faltantes, outliers, consistencia de codificación y cardinalidad antes del modelado.
- Tratar con cuidado variables sensibles, identificadores, fechas y campos de texto.
- Confirmar que la variable objetivo o de referencia se use de acuerdo con el tipo de problema.
- Registrar explícitamente qué columnas se excluyen y justificar si se eliminan por identificador, leakage, privacidad, baja utilidad o disponibilidad operacional.
- Mantener separación entre datos de entrenamiento y evaluación; toda imputación, codificación o escalamiento debe aprenderse solo con entrenamiento.

---

## 5. Plan de Análisis

### 5.1 Análisis Exploratorio de Datos (EDA)

Explorar distribuciones, cardinalidad, correlaciones, outliers, valores faltantes y relación entre variables clave y la decisión de negocio.

**Mínimo esperado:** incluir resumen de calidad de datos, distribución de la variable objetivo o de referencia, análisis de al menos cinco variables relevantes y tres hallazgos escritos en lenguaje de negocio.

### 5.2 Estadística Inferencial

Formular hipótesis de negocio y contrastarlas con pruebas apropiadas: chi-cuadrado, t-test, ANOVA, pruebas no paramétricas o intervalos de confianza según el tipo de variable.

**Mínimo esperado:** plantear al menos dos hipótesis verificables, mostrar el resultado estadístico y explicar si cambia alguna decisión del negocio.

### 5.3 Análisis Multivariante

Aplicar reducción dimensional, análisis de correlación, análisis de correspondencias, embeddings o mapas de segmentos para entender relaciones simultáneas.

**Mínimo esperado:** mostrar relaciones entre variables, redundancias, grupos de variables o patrones multivariados que ayuden a seleccionar features o interpretar segmentos.

### 5.4 Preparación del Dataset y Feature Engineering

Codificar categóricas, escalar numéricas, derivar variables temporales/geográficas, excluir identificadores y controlar leakage.

**Mínimo esperado:** explicar el pipeline final, listar variables eliminadas, describir transformaciones y justificar cualquier variable derivada.

### 5.5 Modelado Predictivo / Segmentación

**Tipo de problema:** Clasificación binaria supervisada
**Variable objetivo o referencia:** `label`

Comparar regresión logística, árbol de decisión, random forest y gradient boosting. Ajustar umbral según costo de falsos positivos y falsos negativos.

**Mínimo esperado:** comparar alternativas, separar validación de entrenamiento, justificar la configuración final y explicar los errores, drivers o segmentos en términos de negocio.

---

## 6. Métricas de Éxito

| Métrica | Uso |
|---|---|
| AUC-ROC | Comparar capacidad discriminativa global |
| Recall clase positiva | Priorizar casos críticos que no deben perderse |
| Precision clase positiva | Controlar falsos positivos y costo operativo |
| F1-score | Balancear precision y recall |
| Matriz de confusión | Traducir errores a impacto de negocio |

---

## 7. Entregables Esperados

1. Notebook reproducible con EDA, limpieza, partición train/test, entrenamiento, evaluación y conclusiones.
2. Pipeline de preparación con variables excluidas, codificación, imputación y escalamiento cuando aplique.
3. Comparación de al menos tres modelos y justificación del modelo recomendado.
4. Selección de umbral operativo con matriz de confusión e impacto esperado para el negocio.
5. Interpretación de las variables más importantes y recomendación concreta de acción.

### 7.1 Formato de Entrega

| Entregable | Contenido mínimo |
|---|---|
| Notebook técnico | Código ejecutable, EDA, limpieza, preparación, modelado o segmentación, métricas y conclusiones. |
| Resumen ejecutivo | Una página o sección final con problema, hallazgos, recomendación, impacto esperado y límites. |
| Tabla de variables usadas | Variables incluidas, excluidas y motivo de exclusión cuando aplique. |
| Evidencia de validación | Métricas, gráficos, matriz de confusión, residuales o perfiles de segmento según el caso. |
| Recomendación accionable | Decisión concreta para el stakeholder, priorización propuesta y riesgos de implementación. |

---

## 8. Criterios de Evaluación

| Criterio | Peso | Qué debe verse en la entrega |
|---|---:|---|
| Entendimiento del negocio | 15% | Problema formulado como decisión real, stakeholder claro y uso esperado de la solución. |
| Calidad y preparación de datos | 20% | Auditoría de faltantes, outliers, tipos, cardinalidad, leakage, variables excluidas y pipeline reproducible. |
| Análisis exploratorio e inferencial | 15% | Hallazgos visuales y estadísticos conectados con hipótesis de negocio, no solo gráficos descriptivos. |
| Modelado o segmentación | 25% | Comparación metodológica, validación correcta, métricas apropiadas y justificación técnica del resultado elegido. |
| Interpretación y recomendación | 20% | Drivers, errores o perfiles explicados en lenguaje de negocio, con acciones concretas y límites de uso. |
| Presentación reproducible | 5% | Notebook ordenado, código ejecutable, conclusiones visibles y anexos suficientes para revisar el trabajo. |

**Criterio específico del caso:** La evaluación debe incluir matriz de confusión, análisis de umbral y discusión del costo de falsos positivos y falsos negativos.

---

## 9. Checklist Antes de Entregar

- [ ] El notebook corre de inicio a fin sin depender de rutas absolutas personales.
- [ ] El dataset usado corresponde a `dataset.csv` del caso y la variable objetivo o referencia coincide con la metadata.
- [ ] Excluí identificadores, variables con leakage y campos que no estarían disponibles al momento de decidir.
- [ ] Documenté decisiones de limpieza, imputación, codificación y escalamiento.
- [ ] Definí la clase positiva, el umbral recomendado y el impacto de la matriz de confusión.
- [ ] Comparé el modelo recomendado contra alternativas y contra una línea base.
- [ ] Incluí al menos tres hallazgos de negocio sustentados por datos.
- [ ] La recomendación final indica qué hacer, con quién hacerlo, por qué y con qué cautelas.
- [ ] La presentación ejecutiva puede leerse sin revisar el código.
