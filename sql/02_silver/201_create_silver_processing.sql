/*
EDRSS V2 — Capa Silver
Objetivo : tipificar, limpiar, marcar anomalías y crear variables determinísticas.
Entrada  : bronze.telecom_raw.
Salidas  : silver.telecom_operations, behavior_features y data_quality_result.
Grano    : una fila limpia y una fila de features por operación.
Regla clave: el TARGET de negocio es 1 cuando la etiqueta fuente es 0.
*/
create table if not exists silver.telecom_operations (
    operation_sk text primary key,
    batch_id uuid not null references bronze.ingestion_batch(batch_id),
    source_row_number bigint not null,
    source_label smallint,
    riesgo_mora smallint check (riesgo_mora in (0, 1)),
    pdate date,
    target_maturity_status text not null
        check (target_maturity_status in ('MATURE', 'QUARANTINE', 'INVALID_DATE')),
    dataset_role text not null
        check (dataset_role in ('TRAIN', 'EMBARGO', 'OOT', 'QUARANTINE', 'OUT_OF_SCOPE')),
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
    payback30 double precision,
    payback90 double precision,
    pcircle text,
    invalid_source_label boolean not null,
    invalid_pdate boolean not null,
    invalid_aon boolean not null,
    invalid_last_rech_date_ma boolean not null,
    invalid_last_rech_date_da boolean not null,
    invalid_maxamnt_loans30 boolean not null,
    invalid_maxamnt_loans90 boolean not null,
    invalid_count_fields boolean not null,
    dq_issue_count smallint not null,
    transformed_at timestamptz not null default current_timestamp,
    transformation_version text not null default 'silver-v1.0.0'
);

create index if not exists ix_silver_operations_batch
    on silver.telecom_operations (batch_id);
create index if not exists ix_silver_operations_date
    on silver.telecom_operations (pdate);
create index if not exists ix_silver_operations_role
    on silver.telecom_operations (dataset_role, target_maturity_status);

create table if not exists silver.behavior_features (
    operation_sk text primary key references silver.telecom_operations(operation_sk),
    batch_id uuid not null references bronze.ingestion_batch(batch_id),
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
    no_main_recharge30 smallint not null,
    no_main_recharge90 smallint not null,
    no_loan30 smallint not null,
    no_data_recharge90 smallint not null,
    recharge_recency_vs_tenure double precision,
    last_amount_vs_median30 double precision,
    log1p_aon double precision,
    log1p_sumamnt_ma_rech30 double precision,
    log1p_sumamnt_ma_rech90 double precision,
    log1p_cnt_ma_rech30 double precision,
    log1p_cnt_ma_rech90 double precision,
    log1p_amnt_loans30 double precision,
    log1p_amnt_loans90 double precision,
    generated_at timestamptz not null default current_timestamp,
    feature_version text not null default 'features-v1.0.0'
);

create index if not exists ix_behavior_features_batch
    on silver.behavior_features (batch_id);

create table if not exists silver.data_quality_result (
    quality_result_id bigint generated always as identity primary key,
    batch_id uuid not null references bronze.ingestion_batch(batch_id),
    layer_name text not null,
    check_name text not null,
    status text not null check (status in ('PASS', 'WARN', 'FAIL')),
    observed_value double precision,
    expected_value text,
    details jsonb not null default '{}'::jsonb,
    checked_at timestamptz not null default current_timestamp
);

create or replace procedure silver.refresh_telecom_operations(p_batch_id uuid)
language plpgsql
as $$
begin
    if not exists (
        select 1 from bronze.ingestion_batch
        where batch_id = p_batch_id and status = 'SUCCESS'
    ) then
        raise exception 'El lote % no existe o no está en SUCCESS', p_batch_id;
    end if;

    delete from silver.behavior_features where batch_id = p_batch_id;
    delete from silver.telecom_operations where batch_id = p_batch_id;
    delete from silver.data_quality_result
    where batch_id = p_batch_id and layer_name = 'SILVER_CLEAN';

    with typed as (
        select
            r.operation_sk, r.batch_id, r.source_row_number,
            silver.try_smallint(r.label) as source_label,
            silver.try_date_dmy(r.pdate) as pdate,
            silver.try_double(r.aon) as aon,
            silver.try_double(r.daily_decr30) as daily_decr30,
            silver.try_double(r.daily_decr90) as daily_decr90,
            silver.try_double(r.rental30) as rental30,
            silver.try_double(r.rental90) as rental90,
            silver.try_double(r.last_rech_date_ma) as last_rech_date_ma,
            silver.try_double(r.last_rech_date_da) as last_rech_date_da,
            silver.try_double(r.last_rech_amt_ma) as last_rech_amt_ma,
            silver.try_double(r.cnt_ma_rech30) as cnt_ma_rech30,
            silver.try_double(r.fr_ma_rech30) as fr_ma_rech30,
            silver.try_double(r.sumamnt_ma_rech30) as sumamnt_ma_rech30,
            silver.try_double(r.medianamnt_ma_rech30) as medianamnt_ma_rech30,
            silver.try_double(r.medianmarechprebal30) as medianmarechprebal30,
            silver.try_double(r.cnt_ma_rech90) as cnt_ma_rech90,
            silver.try_double(r.fr_ma_rech90) as fr_ma_rech90,
            silver.try_double(r.sumamnt_ma_rech90) as sumamnt_ma_rech90,
            silver.try_double(r.medianamnt_ma_rech90) as medianamnt_ma_rech90,
            silver.try_double(r.medianmarechprebal90) as medianmarechprebal90,
            silver.try_double(r.cnt_da_rech30) as cnt_da_rech30,
            silver.try_double(r.fr_da_rech30) as fr_da_rech30,
            silver.try_double(r.cnt_da_rech90) as cnt_da_rech90,
            silver.try_double(r.fr_da_rech90) as fr_da_rech90,
            silver.try_double(r.cnt_loans30) as cnt_loans30,
            silver.try_double(r.amnt_loans30) as amnt_loans30,
            silver.try_double(r.maxamnt_loans30) as maxamnt_loans30,
            silver.try_double(r.medianamnt_loans30) as medianamnt_loans30,
            silver.try_double(r.cnt_loans90) as cnt_loans90,
            silver.try_double(r.amnt_loans90) as amnt_loans90,
            silver.try_double(r.maxamnt_loans90) as maxamnt_loans90,
            silver.try_double(r.medianamnt_loans90) as medianamnt_loans90,
            silver.try_double(r.payback30) as payback30,
            silver.try_double(r.payback90) as payback90,
            r.pcircle
        from bronze.telecom_raw r
        where r.batch_id = p_batch_id
    ), flagged as (
        select t.*,
            (source_label is null or source_label not in (0, 1)) as invalid_source_label,
            (pdate is null) as invalid_pdate,
            (aon is not null and (aon < 0 or aon > 7300)) as invalid_aon,
            (last_rech_date_ma is not null and (last_rech_date_ma < 0 or last_rech_date_ma > 7300)) as invalid_last_rech_date_ma,
            (last_rech_date_da is not null and (last_rech_date_da < 0 or last_rech_date_da > 7300)) as invalid_last_rech_date_da,
            (maxamnt_loans30 is not null and maxamnt_loans30 not in (0, 6, 12)) as invalid_maxamnt_loans30,
            (maxamnt_loans90 is not null and maxamnt_loans90 not in (0, 6, 12)) as invalid_maxamnt_loans90,
            (
                (cnt_ma_rech30 is not null and (cnt_ma_rech30 < 0 or cnt_ma_rech30 <> trunc(cnt_ma_rech30))) or
                (cnt_ma_rech90 is not null and (cnt_ma_rech90 < 0 or cnt_ma_rech90 <> trunc(cnt_ma_rech90))) or
                (cnt_da_rech30 is not null and (cnt_da_rech30 < 0 or cnt_da_rech30 <> trunc(cnt_da_rech30))) or
                (cnt_da_rech90 is not null and (cnt_da_rech90 < 0 or cnt_da_rech90 <> trunc(cnt_da_rech90))) or
                (cnt_loans30 is not null and (cnt_loans30 < 0 or cnt_loans30 <> trunc(cnt_loans30))) or
                (cnt_loans90 is not null and (cnt_loans90 < 0 or cnt_loans90 <> trunc(cnt_loans90)))
            ) as invalid_count_fields
        from typed t
    )
    insert into silver.telecom_operations (
        operation_sk, batch_id, source_row_number, source_label, riesgo_mora,
        pdate, target_maturity_status, dataset_role,
        aon, daily_decr30, daily_decr90, rental30, rental90,
        last_rech_date_ma, last_rech_date_da, last_rech_amt_ma,
        cnt_ma_rech30, fr_ma_rech30, sumamnt_ma_rech30,
        medianamnt_ma_rech30, medianmarechprebal30,
        cnt_ma_rech90, fr_ma_rech90, sumamnt_ma_rech90,
        medianamnt_ma_rech90, medianmarechprebal90,
        cnt_da_rech30, fr_da_rech30, cnt_da_rech90, fr_da_rech90,
        cnt_loans30, amnt_loans30, maxamnt_loans30, medianamnt_loans30,
        cnt_loans90, amnt_loans90, maxamnt_loans90, medianamnt_loans90,
        payback30, payback90, pcircle,
        invalid_source_label, invalid_pdate, invalid_aon,
        invalid_last_rech_date_ma, invalid_last_rech_date_da,
        invalid_maxamnt_loans30, invalid_maxamnt_loans90,
        invalid_count_fields, dq_issue_count
    )
    select
        operation_sk, batch_id, source_row_number, source_label,
        case when pdate <= date '2016-07-23' and source_label in (0, 1)
             then case when source_label = 0 then 1 else 0 end end,
        pdate,
        case when pdate is null then 'INVALID_DATE'
             when pdate <= date '2016-07-23' then 'MATURE'
             else 'QUARANTINE' end,
        case when pdate between date '2016-06-01' and date '2016-07-07' then 'TRAIN'
             when pdate between date '2016-07-08' and date '2016-07-12' then 'EMBARGO'
             when pdate between date '2016-07-13' and date '2016-07-23' then 'OOT'
             when pdate > date '2016-07-23' then 'QUARANTINE'
             else 'OUT_OF_SCOPE' end,
        case when invalid_aon then null else aon end,
        daily_decr30, daily_decr90, rental30, rental90,
        case when invalid_last_rech_date_ma then null else last_rech_date_ma end,
        case when invalid_last_rech_date_da then null else last_rech_date_da end,
        last_rech_amt_ma,
        case when cnt_ma_rech30 is not null and (cnt_ma_rech30 < 0 or cnt_ma_rech30 <> trunc(cnt_ma_rech30)) then null else cnt_ma_rech30 end,
        fr_ma_rech30, sumamnt_ma_rech30, medianamnt_ma_rech30, medianmarechprebal30,
        case when cnt_ma_rech90 is not null and (cnt_ma_rech90 < 0 or cnt_ma_rech90 <> trunc(cnt_ma_rech90)) then null else cnt_ma_rech90 end,
        fr_ma_rech90, sumamnt_ma_rech90, medianamnt_ma_rech90, medianmarechprebal90,
        case when cnt_da_rech30 is not null and (cnt_da_rech30 < 0 or cnt_da_rech30 <> trunc(cnt_da_rech30)) then null else cnt_da_rech30 end,
        fr_da_rech30,
        case when cnt_da_rech90 is not null and (cnt_da_rech90 < 0 or cnt_da_rech90 <> trunc(cnt_da_rech90)) then null else cnt_da_rech90 end,
        fr_da_rech90,
        case when cnt_loans30 is not null and (cnt_loans30 < 0 or cnt_loans30 <> trunc(cnt_loans30)) then null else cnt_loans30 end,
        amnt_loans30,
        case when invalid_maxamnt_loans30 then null else maxamnt_loans30 end,
        medianamnt_loans30,
        case when cnt_loans90 is not null and (cnt_loans90 < 0 or cnt_loans90 <> trunc(cnt_loans90)) then null else cnt_loans90 end,
        amnt_loans90,
        case when invalid_maxamnt_loans90 then null else maxamnt_loans90 end,
        medianamnt_loans90, payback30, payback90, nullif(btrim(pcircle), ''),
        invalid_source_label, invalid_pdate, invalid_aon,
        invalid_last_rech_date_ma, invalid_last_rech_date_da,
        invalid_maxamnt_loans30, invalid_maxamnt_loans90,
        invalid_count_fields,
        invalid_source_label::int + invalid_pdate::int + invalid_aon::int +
        invalid_last_rech_date_ma::int + invalid_last_rech_date_da::int +
        invalid_maxamnt_loans30::int + invalid_maxamnt_loans90::int +
        invalid_count_fields::int
    from flagged;

    insert into silver.data_quality_result
        (batch_id, layer_name, check_name, status, observed_value, expected_value)
    select p_batch_id, 'SILVER_CLEAN', 'row_count_matches_bronze',
           case when b.n = s.n then 'PASS' else 'FAIL' end,
           s.n, b.n::text
    from (select count(*) n from bronze.telecom_raw where batch_id = p_batch_id) b,
         (select count(*) n from silver.telecom_operations where batch_id = p_batch_id) s;

    insert into silver.data_quality_result
        (batch_id, layer_name, check_name, status, observed_value, expected_value)
    select p_batch_id, 'SILVER_CLEAN', 'unparseable_dates',
           case when count(*) = 0 then 'PASS' else 'FAIL' end,
           count(*), '0'
    from silver.telecom_operations
    where batch_id = p_batch_id and invalid_pdate;

    insert into silver.data_quality_result
        (batch_id, layer_name, check_name, status, observed_value, expected_value)
    select p_batch_id, 'SILVER_CLEAN', 'quarantine_rows', 'WARN',
           count(*), 'Expected because TARGET is immature after 2016-07-23'
    from silver.telecom_operations
    where batch_id = p_batch_id and target_maturity_status = 'QUARANTINE';
end;
$$;

create or replace procedure silver.refresh_behavior_features(p_batch_id uuid)
language plpgsql
as $$
begin
    if not exists (
        select 1 from silver.telecom_operations where batch_id = p_batch_id
    ) then
        raise exception 'No existe Silver clean para el lote %', p_batch_id;
    end if;

    delete from silver.behavior_features where batch_id = p_batch_id;
    delete from silver.data_quality_result
    where batch_id = p_batch_id and layer_name = 'SILVER_FEATURES';

    insert into silver.behavior_features (
        operation_sk, batch_id,
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
        operation_sk, batch_id,
        silver.safe_divide(sumamnt_ma_rech30, sumamnt_ma_rech90),
        silver.safe_divide(cnt_ma_rech30, cnt_ma_rech90),
        silver.safe_divide(amnt_loans30, amnt_loans90),
        silver.safe_divide(cnt_loans30, cnt_loans90),
        silver.safe_divide(cnt_da_rech30, cnt_da_rech90),
        3 * silver.safe_divide(sumamnt_ma_rech30, sumamnt_ma_rech90),
        3 * silver.safe_divide(cnt_ma_rech30, cnt_ma_rech90),
        3 * silver.safe_divide(amnt_loans30, amnt_loans90),
        3 * silver.safe_divide(cnt_loans30, cnt_loans90),
        3 * silver.safe_divide(daily_decr30, daily_decr90),
        3 * silver.safe_divide(rental30, rental90),
        silver.safe_divide(sumamnt_ma_rech30, cnt_ma_rech30),
        silver.safe_divide(sumamnt_ma_rech90, cnt_ma_rech90),
        silver.safe_divide(amnt_loans30, cnt_loans30),
        silver.safe_divide(amnt_loans90, cnt_loans90),
        case when cnt_ma_rech30 = 0 then 1 else 0 end,
        case when cnt_ma_rech90 = 0 then 1 else 0 end,
        case when cnt_loans30 = 0 then 1 else 0 end,
        case when cnt_da_rech90 = 0 then 1 else 0 end,
        silver.safe_divide(last_rech_date_ma, aon + 1),
        silver.safe_divide(last_rech_amt_ma, medianamnt_ma_rech30 + 1),
        case when aon is null then null else ln(1 + greatest(aon, 0)) end,
        case when sumamnt_ma_rech30 is null then null else ln(1 + greatest(sumamnt_ma_rech30, 0)) end,
        case when sumamnt_ma_rech90 is null then null else ln(1 + greatest(sumamnt_ma_rech90, 0)) end,
        case when cnt_ma_rech30 is null then null else ln(1 + greatest(cnt_ma_rech30, 0)) end,
        case when cnt_ma_rech90 is null then null else ln(1 + greatest(cnt_ma_rech90, 0)) end,
        case when amnt_loans30 is null then null else ln(1 + greatest(amnt_loans30, 0)) end,
        case when amnt_loans90 is null then null else ln(1 + greatest(amnt_loans90, 0)) end
    from silver.telecom_operations
    where batch_id = p_batch_id;

    insert into silver.data_quality_result
        (batch_id, layer_name, check_name, status, observed_value, expected_value)
    select p_batch_id, 'SILVER_FEATURES', 'row_count_matches_clean',
           case when c.n = f.n then 'PASS' else 'FAIL' end,
           f.n, c.n::text
    from (select count(*) n from silver.telecom_operations where batch_id = p_batch_id) c,
         (select count(*) n from silver.behavior_features where batch_id = p_batch_id) f;
end;
$$;
