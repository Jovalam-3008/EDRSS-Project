/*
EDRSS V2 — Productos Gold
Objetivo : publicar los contratos certificados para ML, scoring y KPIs.
Entradas : silver.telecom_operations y silver.behavior_features.
Salidas  : ml_features, ml_training, ml_scoring, registro y métricas de modelos.
Grano    : una fila por operación; una ejecución por modelo en model_registry.
*/
create table if not exists gold.ml_features (
    operation_sk text primary key,
    batch_id uuid not null references bronze.ingestion_batch(batch_id),
    pdate date not null,
    riesgo_mora smallint check (riesgo_mora in (0, 1)),
    target_maturity_status text not null,
    dataset_role text not null,
    aon double precision,
    daily_decr30 double precision,
    daily_decr90 double precision,
    rental30 double precision,
    rental90 double precision,
    last_rech_date_ma double precision,
    last_rech_date_da double precision,
    last_rech_amt_ma double precision,
    cnt_ma_rech30 double precision,
    fr_ma_rech30 double precision,
    sumamnt_ma_rech30 double precision,
    medianamnt_ma_rech30 double precision,
    medianmarechprebal30 double precision,
    cnt_ma_rech90 double precision,
    fr_ma_rech90 double precision,
    sumamnt_ma_rech90 double precision,
    medianamnt_ma_rech90 double precision,
    medianmarechprebal90 double precision,
    cnt_da_rech30 double precision,
    fr_da_rech30 double precision,
    cnt_da_rech90 double precision,
    fr_da_rech90 double precision,
    cnt_loans30 double precision,
    amnt_loans30 double precision,
    maxamnt_loans30 double precision,
    medianamnt_loans30 double precision,
    cnt_loans90 double precision,
    amnt_loans90 double precision,
    maxamnt_loans90 double precision,
    medianamnt_loans90 double precision,
    share_recharge_amount_30_90 double precision,
    share_recharge_count_30_90 double precision,
    share_loan_amount_30_90 double precision,
    share_loan_count_30_90 double precision,
    share_data_recharge_count_30_90 double precision,
    recharge_amount_intensity double precision,
    recharge_count_intensity double precision,
    loan_amount_intensity double precision,
    loan_count_intensity double precision,
    daily_decr_intensity double precision,
    rental_intensity double precision,
    recharge_amount_per_event30 double precision,
    recharge_amount_per_event90 double precision,
    loan_amount_per_event30 double precision,
    loan_amount_per_event90 double precision,
    no_main_recharge30 smallint,
    no_main_recharge90 smallint,
    no_loan30 smallint,
    no_data_recharge90 smallint,
    recharge_recency_vs_tenure double precision,
    last_amount_vs_median30 double precision,
    log1p_aon double precision,
    log1p_sumamnt_ma_rech30 double precision,
    log1p_sumamnt_ma_rech90 double precision,
    log1p_cnt_ma_rech30 double precision,
    log1p_cnt_ma_rech90 double precision,
    log1p_amnt_loans30 double precision,
    log1p_amnt_loans90 double precision,
    source_version text not null default 'openml-43745-md5-5fc2b932',
    silver_version text not null default 'silver-v1.0.0',
    feature_version text not null default 'features-v1.0.0',
    published_at timestamptz not null default current_timestamp
);

create index if not exists ix_ml_features_batch on gold.ml_features(batch_id);
create index if not exists ix_ml_features_date on gold.ml_features(pdate);
create index if not exists ix_ml_features_role on gold.ml_features(dataset_role);

create or replace view gold.ml_training
with (security_invoker = true)
as
select *
from gold.ml_features
where target_maturity_status = 'MATURE'
  and dataset_role in ('TRAIN', 'EMBARGO', 'OOT')
  and riesgo_mora is not null;

comment on view gold.ml_training is
    'Consumible certificado para entrenamiento temporal: 58 features, TARGET maduro y roles congelados.';

create or replace view gold.ml_scoring
with (security_invoker = true)
as
select *
from gold.ml_features
where target_maturity_status = 'QUARANTINE'
  and riesgo_mora is null;

comment on view gold.ml_scoring is
    'Población sin TARGET maduro para scoring o cuarentena; nunca se usa para evaluación supervisada.';

create table if not exists gold.model_registry (
    model_run_id uuid primary key default gen_random_uuid(),
    model_name text not null,
    model_version text not null,
    feature_version text not null,
    training_batch_id uuid references bronze.ingestion_batch(batch_id),
    status text not null check (status in ('CANDIDATE', 'ACTIVE', 'RETIRED', 'FAILED')),
    trained_at timestamptz not null default current_timestamp,
    threshold double precision,
    artifact_uri text,
    parameters jsonb not null default '{}'::jsonb,
    notes text,
    unique (model_name, model_version)
);

create unique index if not exists ux_one_active_model
    on gold.model_registry ((status)) where status = 'ACTIVE';

create table if not exists gold.model_predictions (
    model_run_id uuid not null references gold.model_registry(model_run_id),
    operation_sk text not null references gold.ml_features(operation_sk),
    batch_id uuid not null references bronze.ingestion_batch(batch_id),
    pdate date not null,
    dataset_role text not null,
    riesgo_mora smallint,
    risk_score double precision not null check (risk_score between 0 and 1),
    predicted_label smallint check (predicted_label in (0, 1)),
    risk_band text not null check (risk_band in ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    priority_rank bigint,
    scored_at timestamptz not null default current_timestamp,
    primary key (model_run_id, operation_sk)
);

create index if not exists ix_predictions_priority
    on gold.model_predictions(model_run_id, priority_rank);
create index if not exists ix_predictions_date
    on gold.model_predictions(pdate);

create table if not exists gold.model_metrics (
    metric_id bigint generated always as identity primary key,
    model_run_id uuid not null references gold.model_registry(model_run_id),
    evaluation_scope text not null,
    fold_number smallint,
    period_start date,
    period_end date,
    metric_name text not null,
    metric_value double precision not null,
    measured_at timestamptz not null default current_timestamp,
    unique (model_run_id, evaluation_scope, fold_number, metric_name)
);

create table if not exists gold.model_capacity_metrics (
    capacity_metric_id bigint generated always as identity primary key,
    model_run_id uuid not null references gold.model_registry(model_run_id),
    evaluation_scope text not null,
    capacity_fraction double precision not null check (capacity_fraction > 0 and capacity_fraction <= 1),
    contacts bigint not null,
    positives_captured bigint,
    precision_at_k double precision,
    recall_at_k double precision,
    lift_at_k double precision,
    measured_at timestamptz not null default current_timestamp,
    unique (model_run_id, evaluation_scope, capacity_fraction)
);

create table if not exists gold.model_feature_importance (
    model_run_id uuid not null references gold.model_registry(model_run_id),
    feature_name text not null,
    importance_type text not null,
    importance_value double precision not null,
    importance_std double precision,
    feature_rank smallint,
    measured_at timestamptz not null default current_timestamp,
    primary key (model_run_id, feature_name, importance_type)
);

create table if not exists gold.executive_kpi_snapshot (
    snapshot_id bigint generated always as identity primary key,
    batch_id uuid not null references bronze.ingestion_batch(batch_id),
    snapshot_date date not null,
    kpi_name text not null,
    kpi_value double precision,
    kpi_unit text not null,
    tier text not null check (tier in ('S', 'A', 'B', 'C')),
    is_simulated boolean not null default false,
    assumption text,
    calculated_at timestamptz not null default current_timestamp,
    unique (batch_id, snapshot_date, kpi_name)
);

create or replace procedure gold.refresh_ml_features(p_batch_id uuid)
language plpgsql
as $$
begin
    if not exists (
        select 1 from silver.behavior_features where batch_id = p_batch_id
    ) then
        raise exception 'No existen features Silver para el lote %', p_batch_id;
    end if;

    delete from gold.ml_features where batch_id = p_batch_id;
    delete from silver.data_quality_result
    where batch_id = p_batch_id and layer_name = 'GOLD';

    insert into gold.ml_features (
        operation_sk, batch_id, pdate, riesgo_mora,
        target_maturity_status, dataset_role,
        aon, daily_decr30, daily_decr90, rental30, rental90,
        last_rech_date_ma, last_rech_date_da, last_rech_amt_ma,
        cnt_ma_rech30, fr_ma_rech30, sumamnt_ma_rech30,
        medianamnt_ma_rech30, medianmarechprebal30,
        cnt_ma_rech90, fr_ma_rech90, sumamnt_ma_rech90,
        medianamnt_ma_rech90, medianmarechprebal90,
        cnt_da_rech30, fr_da_rech30, cnt_da_rech90, fr_da_rech90,
        cnt_loans30, amnt_loans30, maxamnt_loans30, medianamnt_loans30,
        cnt_loans90, amnt_loans90, maxamnt_loans90, medianamnt_loans90,
        share_recharge_amount_30_90, share_recharge_count_30_90,
        share_loan_amount_30_90, share_loan_count_30_90,
        share_data_recharge_count_30_90,
        recharge_amount_intensity, recharge_count_intensity,
        loan_amount_intensity, loan_count_intensity,
        daily_decr_intensity, rental_intensity,
        recharge_amount_per_event30, recharge_amount_per_event90,
        loan_amount_per_event30, loan_amount_per_event90,
        no_main_recharge30, no_main_recharge90, no_loan30, no_data_recharge90,
        recharge_recency_vs_tenure, last_amount_vs_median30,
        log1p_aon, log1p_sumamnt_ma_rech30, log1p_sumamnt_ma_rech90,
        log1p_cnt_ma_rech30, log1p_cnt_ma_rech90,
        log1p_amnt_loans30, log1p_amnt_loans90
    )
    select
        o.operation_sk, o.batch_id, o.pdate, o.riesgo_mora,
        o.target_maturity_status, o.dataset_role,
        o.aon, o.daily_decr30, o.daily_decr90, o.rental30, o.rental90,
        o.last_rech_date_ma, o.last_rech_date_da, o.last_rech_amt_ma,
        o.cnt_ma_rech30, o.fr_ma_rech30, o.sumamnt_ma_rech30,
        o.medianamnt_ma_rech30, o.medianmarechprebal30,
        o.cnt_ma_rech90, o.fr_ma_rech90, o.sumamnt_ma_rech90,
        o.medianamnt_ma_rech90, o.medianmarechprebal90,
        o.cnt_da_rech30, o.fr_da_rech30, o.cnt_da_rech90, o.fr_da_rech90,
        o.cnt_loans30, o.amnt_loans30, o.maxamnt_loans30, o.medianamnt_loans30,
        o.cnt_loans90, o.amnt_loans90, o.maxamnt_loans90, o.medianamnt_loans90,
        f.share_recharge_amount_30_90, f.share_recharge_count_30_90,
        f.share_loan_amount_30_90, f.share_loan_count_30_90,
        f.share_data_recharge_count_30_90,
        f.recharge_amount_intensity, f.recharge_count_intensity,
        f.loan_amount_intensity, f.loan_count_intensity,
        f.daily_decr_intensity, f.rental_intensity,
        f.recharge_amount_per_event30, f.recharge_amount_per_event90,
        f.loan_amount_per_event30, f.loan_amount_per_event90,
        f.no_main_recharge30, f.no_main_recharge90, f.no_loan30, f.no_data_recharge90,
        f.recharge_recency_vs_tenure, f.last_amount_vs_median30,
        f.log1p_aon, f.log1p_sumamnt_ma_rech30, f.log1p_sumamnt_ma_rech90,
        f.log1p_cnt_ma_rech30, f.log1p_cnt_ma_rech90,
        f.log1p_amnt_loans30, f.log1p_amnt_loans90
    from silver.telecom_operations o
    join silver.behavior_features f using (operation_sk, batch_id)
    where o.batch_id = p_batch_id
      and o.pdate is not null;

    insert into silver.data_quality_result
        (batch_id, layer_name, check_name, status, observed_value, expected_value)
    select p_batch_id, 'GOLD', 'row_count_matches_valid_silver',
           case when s.n = g.n then 'PASS' else 'FAIL' end,
           g.n, s.n::text
    from (
        select count(*) n from silver.telecom_operations
        where batch_id = p_batch_id and pdate is not null
    ) s,
    (select count(*) n from gold.ml_features where batch_id = p_batch_id) g;

    insert into silver.data_quality_result
        (batch_id, layer_name, check_name, status, observed_value, expected_value)
    select p_batch_id, 'GOLD', 'model_feature_count',
           case when count(*) = 58 then 'PASS' else 'FAIL' end,
           count(*), '58'
    from information_schema.columns
    where table_schema = 'gold' and table_name = 'ml_features'
      and column_name not in (
        'operation_sk', 'batch_id', 'pdate', 'riesgo_mora',
        'target_maturity_status', 'dataset_role', 'source_version',
        'silver_version', 'feature_version', 'published_at'
      );
end;
$$;

create or replace procedure gold.refresh_executive_kpis(p_batch_id uuid)
language plpgsql
as $$
declare
    v_snapshot_date date;
begin
    select max(pdate) into v_snapshot_date
    from gold.ml_features where batch_id = p_batch_id;

    if v_snapshot_date is null then
        raise exception 'Gold no contiene datos para el lote %', p_batch_id;
    end if;

    delete from gold.executive_kpi_snapshot where batch_id = p_batch_id;

    insert into gold.executive_kpi_snapshot
        (batch_id, snapshot_date, kpi_name, kpi_value, kpi_unit, tier)
    select p_batch_id, v_snapshot_date, 'total_operations', count(*), 'operations', 'S'
    from gold.ml_features where batch_id = p_batch_id
    union all
    select p_batch_id, v_snapshot_date, 'mature_operations', count(*), 'operations', 'S'
    from gold.ml_training where batch_id = p_batch_id
    union all
    select p_batch_id, v_snapshot_date, 'quarantine_operations', count(*), 'operations', 'S'
    from gold.ml_scoring where batch_id = p_batch_id
    union all
    select p_batch_id, v_snapshot_date, 'mature_delinquency_rate', avg(riesgo_mora), 'ratio', 'S'
    from gold.ml_training where batch_id = p_batch_id
    union all
    select p_batch_id, v_snapshot_date, 'data_quality_issue_rate', avg((dq_issue_count > 0)::int), 'ratio', 'C'
    from silver.telecom_operations where batch_id = p_batch_id;
end;
$$;
