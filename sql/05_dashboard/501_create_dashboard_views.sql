/*
EDRSS V2 — Vistas base del dashboard
Objetivo : exponer únicamente información certificada de Gold.
Entrada  : productos Gold.
Salidas  : vistas api.dashboard_*.
Seguridad: Bronze, Silver y Gold no se exponen a usuarios del dashboard.
*/
create or replace view api.dashboard_executive
with (security_invoker = true)
as
select s.*
from gold.executive_kpi_snapshot s
join (
    select kpi_name, max(calculated_at) as latest
    from gold.executive_kpi_snapshot
    group by kpi_name
) x on x.kpi_name = s.kpi_name and x.latest = s.calculated_at;

create or replace view api.dashboard_portfolio_daily
with (security_invoker = true)
as
select
    pdate,
    dataset_role,
    target_maturity_status,
    count(*) as operations,
    sum(riesgo_mora) filter (where riesgo_mora is not null) as delinquent_operations,
    avg(riesgo_mora) filter (where riesgo_mora is not null) as delinquency_rate,
    avg(cnt_ma_rech30) as avg_recharges_30d,
    avg(amnt_loans30) as avg_loan_amount_30d,
    avg(no_main_recharge30) as rate_without_main_recharge_30d
from gold.ml_features
group by pdate, dataset_role, target_maturity_status;

create or replace view api.dashboard_capacity_story
with (security_invoker = true)
as
select
    r.model_name,
    r.model_version,
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

create or replace view api.dashboard_model_health
with (security_invoker = true)
as
select
    r.model_name,
    r.model_version,
    r.status,
    m.evaluation_scope,
    m.fold_number,
    m.period_start,
    m.period_end,
    m.metric_name,
    m.metric_value,
    m.measured_at
from gold.model_metrics m
join gold.model_registry r using (model_run_id)
where r.status in ('ACTIVE', 'CANDIDATE');

create or replace view api.dashboard_priority_queue
with (security_invoker = true)
as
select
    p.operation_sk,
    p.pdate,
    p.risk_score,
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

revoke all on schema bronze from anon, authenticated;
revoke all on schema silver from anon, authenticated;
revoke all on schema gold from anon, authenticated;

grant usage on schema api to authenticated, service_role;
grant select on all tables in schema api to authenticated, service_role;
alter default privileges for role postgres in schema api
    grant select on tables to authenticated, service_role;
