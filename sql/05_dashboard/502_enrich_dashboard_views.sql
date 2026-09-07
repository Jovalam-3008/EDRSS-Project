/*
EDRSS V2 — Detalle analítico del dashboard
Objetivo : completar métricas, importancia de variables y cola de cobranza.
Entrada  : resultados del modelo almacenados en Gold.
Salida   : vistas API enriquecidas.
*/
drop view if exists api.dashboard_capacity_story;
drop view if exists api.dashboard_priority_queue;

create or replace view api.dashboard_capacity_story
with (security_invoker = true)
as
select
    r.model_name,
    r.model_version,
    r.status,
    c.evaluation_scope,
    c.capacity_fraction,
    c.contacts,
    c.positives_captured,
    c.precision_at_k,
    c.recall_at_k,
    c.lift_at_k,
    c.measured_at
from gold.model_capacity_metrics c
join gold.model_registry r using (model_run_id)
where r.status in ('ACTIVE', 'CANDIDATE');

create or replace view api.dashboard_priority_queue
with (security_invoker = true)
as
select
    r.model_name,
    r.model_version,
    p.operation_sk,
    p.pdate,
    p.dataset_role,
    p.riesgo_mora,
    p.risk_score,
    p.predicted_label,
    p.risk_band,
    p.priority_rank,
    f.aon,
    f.cnt_ma_rech30,
    f.sumamnt_ma_rech30,
    f.cnt_loans30,
    f.amnt_loans30,
    f.no_main_recharge30,
    f.no_loan30
from gold.model_predictions p
join gold.model_registry r using (model_run_id)
join gold.ml_features f using (operation_sk, batch_id)
where r.status = 'ACTIVE';

create or replace view api.dashboard_feature_importance
with (security_invoker = true)
as
select
    r.model_name,
    r.model_version,
    i.feature_name,
    i.importance_type,
    i.importance_value,
    i.importance_std,
    i.feature_rank,
    i.measured_at
from gold.model_feature_importance i
join gold.model_registry r using (model_run_id)
where r.status = 'ACTIVE';

create or replace view api.dashboard_score_distribution
with (security_invoker = true)
as
select
    r.model_name,
    r.model_version,
    p.dataset_role,
    p.pdate,
    p.risk_band,
    count(*) as operations,
    avg(p.risk_score) as avg_risk_score,
    min(p.risk_score) as min_risk_score,
    max(p.risk_score) as max_risk_score
from gold.model_predictions p
join gold.model_registry r using (model_run_id)
where r.status = 'ACTIVE'
group by r.model_name, r.model_version, p.dataset_role, p.pdate, p.risk_band;

grant select on all tables in schema api to authenticated, service_role;
