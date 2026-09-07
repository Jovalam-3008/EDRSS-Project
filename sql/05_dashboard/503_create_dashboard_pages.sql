/*
EDRSS V2 — Marts de las páginas del dashboard
Objetivo : una vista simple por hoja del tablero, sin lógica de limpieza en la UI.
Entradas : tablas y vistas certificadas de Gold.
Salidas  : api.page_*.
*/

-- Hoja 1: Resumen ejecutivo. Un registro con los indicadores vigentes.
create or replace view api.page_executive_summary
with (security_invoker = true)
as
with portfolio as (
    select
        count(*) as total_operations,
        count(*) filter (where target_maturity_status = 'MATURE') as mature_operations,
        count(*) filter (where target_maturity_status = 'QUARANTINE') as scoring_population,
        avg(riesgo_mora) filter (where riesgo_mora is not null) as delinquency_rate
    from gold.ml_features
), active as (
    select model_run_id, model_name, model_version, threshold, trained_at
    from gold.active_model
), oot_auc as (
    select model_run_id, metric_value as oot_roc_auc
    from gold.model_metrics
    where evaluation_scope = 'OOT' and metric_name = 'roc_auc'
), capacity as (
    select
        model_run_id,
        recall_at_k as recall_at_10,
        precision_at_k as precision_at_10,
        lift_at_k as lift_at_10
    from gold.model_capacity_metrics
    where evaluation_scope = 'OOT' and capacity_fraction = 0.10
)
select
    p.*,
    a.model_name,
    a.model_version,
    a.threshold,
    a.trained_at,
    m.oot_roc_auc,
    c.recall_at_10,
    c.precision_at_10,
    c.lift_at_10
from portfolio p
left join active a on true
left join oot_auc m using (model_run_id)
left join capacity c using (model_run_id);

-- Hoja 2: Riesgo y mora. Un registro por fecha y rol temporal.
create or replace view api.page_risk_and_delinquency
with (security_invoker = true)
as
select
    pdate,
    dataset_role,
    count(*) as operations,
    count(*) filter (where riesgo_mora = 1) as delinquent_operations,
    avg(riesgo_mora) filter (where riesgo_mora is not null) as delinquency_rate,
    avg(amnt_loans30) as avg_loan_amount_30d,
    avg(cnt_loans30) as avg_loans_30d
from gold.ml_features
group by pdate, dataset_role;

-- Hoja 3: Comportamiento. Comparación de perfiles con y sin mora.
create or replace view api.page_customer_behavior
with (security_invoker = true)
as
select
    pdate,
    riesgo_mora,
    count(*) as operations,
    avg(aon) as avg_tenure,
    avg(cnt_ma_rech30) as avg_main_recharges_30d,
    avg(sumamnt_ma_rech30) as avg_recharge_amount_30d,
    avg(cnt_loans30) as avg_loans_30d,
    avg(amnt_loans30) as avg_loan_amount_30d,
    avg(no_main_recharge30) as rate_without_recharge_30d,
    avg(no_loan30) as rate_without_loan_30d
from gold.ml_training
group by pdate, riesgo_mora;

-- Hoja 4: Modelo predictivo. Métricas y estabilidad del modelo activo.
create or replace view api.page_predictive_model
with (security_invoker = true)
as
select
    m.model_name,
    m.model_version,
    m.trained_at,
    x.evaluation_scope,
    x.fold_number,
    x.period_start,
    x.period_end,
    x.metric_name,
    x.metric_value,
    x.measured_at
from gold.active_model m
join gold.model_metrics x using (model_run_id);

-- Hoja 5: Priorización. Cola accionable ordenada por riesgo.
create or replace view api.page_collection_priority
with (security_invoker = true)
as
select *
from api.dashboard_priority_queue
where dataset_role = 'SCORING';

grant select on all tables in schema api to authenticated, service_role;
