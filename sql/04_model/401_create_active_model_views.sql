/*
EDRSS V2 — Modelo activo
Objetivo : ofrecer un punto único para consultar el modelo vigente y sus scores.
Entradas : gold.model_registry, gold.model_predictions.
Salidas  : gold.active_model, gold.active_predictions.
Grano    : un modelo activo / una predicción por operación.
*/

create or replace view gold.active_model
with (security_invoker = true)
as
select
    model_run_id,
    model_name,
    model_version,
    feature_version,
    training_batch_id,
    trained_at,
    threshold,
    artifact_uri,
    parameters,
    notes
from gold.model_registry
where status = 'ACTIVE';

create or replace view gold.active_predictions
with (security_invoker = true)
as
select p.*
from gold.model_predictions p
join gold.active_model m using (model_run_id);

comment on view gold.active_model is
    'Único modelo aprobado para scoring y dashboard.';
comment on view gold.active_predictions is
    'Predicciones correspondientes al modelo activo.';

