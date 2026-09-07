/*
EDRSS V2 — Capa Bronze
Objetivo : conservar una copia fiel del CSV y la trazabilidad de cada ingesta.
Entrada  : dataset.csv, cargado posteriormente por Python.
Salidas  : bronze.ingestion_batch, source_column_catalog y telecom_raw.
Grano    : una fila por operación original del archivo.
*/
create table if not exists bronze.ingestion_batch (
    batch_id uuid primary key,
    project_name text not null default 'Early Delinquency Risk Scoring System (EDRSS)',
    source_file_name text not null,
    source_file_hash char(32) not null,
    source_row_count bigint,
    loaded_row_count bigint,
    rejected_row_count bigint,
    status text not null check (status in ('RUNNING', 'SUCCESS', 'FAILED')),
    started_at timestamptz not null default current_timestamp,
    completed_at timestamptz,
    error_message text,
    created_by text not null default current_user
);

create index if not exists ix_ingestion_batch_hash_status
    on bronze.ingestion_batch (source_file_hash, status);

create table if not exists bronze.source_column_catalog (
    source_name text not null,
    ordinal_position smallint not null,
    column_name text not null,
    raw_data_type text not null default 'text',
    business_description text,
    is_target boolean not null default false,
    primary key (source_name, column_name),
    unique (source_name, ordinal_position)
);

create table if not exists bronze.telecom_raw (
    operation_sk text generated always as (
        md5(source_file_hash || ':' || source_row_number::text)
    ) stored,
    batch_id uuid not null references bronze.ingestion_batch(batch_id),
    source_row_number bigint not null,
    source_file_name text not null,
    source_file_hash char(32) not null,
    label text,
    aon text,
    daily_decr30 text,
    daily_decr90 text,
    rental30 text,
    rental90 text,
    last_rech_date_ma text,
    last_rech_date_da text,
    last_rech_amt_ma text,
    cnt_ma_rech30 text,
    fr_ma_rech30 text,
    sumamnt_ma_rech30 text,
    medianamnt_ma_rech30 text,
    medianmarechprebal30 text,
    cnt_ma_rech90 text,
    fr_ma_rech90 text,
    sumamnt_ma_rech90 text,
    medianamnt_ma_rech90 text,
    medianmarechprebal90 text,
    cnt_da_rech30 text,
    fr_da_rech30 text,
    cnt_da_rech90 text,
    fr_da_rech90 text,
    cnt_loans30 text,
    amnt_loans30 text,
    maxamnt_loans30 text,
    medianamnt_loans30 text,
    cnt_loans90 text,
    amnt_loans90 text,
    maxamnt_loans90 text,
    medianamnt_loans90 text,
    payback30 text,
    payback90 text,
    pcircle text,
    pdate text,
    ingested_at timestamptz not null default current_timestamp,
    primary key (operation_sk),
    unique (batch_id, source_row_number)
);

create index if not exists ix_telecom_raw_batch
    on bronze.telecom_raw (batch_id);

insert into bronze.source_column_catalog
    (source_name, ordinal_position, column_name, business_description, is_target)
values
    ('delinquency_telecom', 1, 'label', 'Etiqueta original: 0 representa fallo de repago', true),
    ('delinquency_telecom', 2, 'aon', 'Antigüedad de la línea', false),
    ('delinquency_telecom', 3, 'daily_decr30', 'Actividad de consumo acumulada a 30 días', false),
    ('delinquency_telecom', 4, 'daily_decr90', 'Actividad de consumo acumulada a 90 días', false),
    ('delinquency_telecom', 5, 'rental30', 'Uso o renta acumulada a 30 días', false),
    ('delinquency_telecom', 6, 'rental90', 'Uso o renta acumulada a 90 días', false),
    ('delinquency_telecom', 7, 'last_rech_date_ma', 'Recencia de última recarga principal', false),
    ('delinquency_telecom', 8, 'last_rech_date_da', 'Recencia de última recarga de datos', false),
    ('delinquency_telecom', 9, 'last_rech_amt_ma', 'Monto de última recarga principal', false),
    ('delinquency_telecom', 10, 'cnt_ma_rech30', 'Cantidad de recargas principales a 30 días', false),
    ('delinquency_telecom', 11, 'fr_ma_rech30', 'Frecuencia de recarga principal a 30 días', false),
    ('delinquency_telecom', 12, 'sumamnt_ma_rech30', 'Monto de recargas principales a 30 días', false),
    ('delinquency_telecom', 13, 'medianamnt_ma_rech30', 'Mediana de recarga principal a 30 días', false),
    ('delinquency_telecom', 14, 'medianmarechprebal30', 'Mediana de saldo previo a 30 días', false),
    ('delinquency_telecom', 15, 'cnt_ma_rech90', 'Cantidad de recargas principales a 90 días', false),
    ('delinquency_telecom', 16, 'fr_ma_rech90', 'Frecuencia de recarga principal a 90 días', false),
    ('delinquency_telecom', 17, 'sumamnt_ma_rech90', 'Monto de recargas principales a 90 días', false),
    ('delinquency_telecom', 18, 'medianamnt_ma_rech90', 'Mediana de recarga principal a 90 días', false),
    ('delinquency_telecom', 19, 'medianmarechprebal90', 'Mediana de saldo previo a 90 días', false),
    ('delinquency_telecom', 20, 'cnt_da_rech30', 'Cantidad de recargas de datos a 30 días', false),
    ('delinquency_telecom', 21, 'fr_da_rech30', 'Frecuencia de recarga de datos a 30 días', false),
    ('delinquency_telecom', 22, 'cnt_da_rech90', 'Cantidad de recargas de datos a 90 días', false),
    ('delinquency_telecom', 23, 'fr_da_rech90', 'Frecuencia de recarga de datos a 90 días', false),
    ('delinquency_telecom', 24, 'cnt_loans30', 'Cantidad de préstamos a 30 días', false),
    ('delinquency_telecom', 25, 'amnt_loans30', 'Monto de préstamos a 30 días', false),
    ('delinquency_telecom', 26, 'maxamnt_loans30', 'Monto máximo de préstamos a 30 días', false),
    ('delinquency_telecom', 27, 'medianamnt_loans30', 'Mediana de préstamos a 30 días', false),
    ('delinquency_telecom', 28, 'cnt_loans90', 'Cantidad de préstamos a 90 días', false),
    ('delinquency_telecom', 29, 'amnt_loans90', 'Monto de préstamos a 90 días', false),
    ('delinquency_telecom', 30, 'maxamnt_loans90', 'Monto máximo de préstamos a 90 días', false),
    ('delinquency_telecom', 31, 'medianamnt_loans90', 'Mediana de préstamos a 90 días', false),
    ('delinquency_telecom', 32, 'payback30', 'Indicador de repago a 30 días; excluido del modelo base', false),
    ('delinquency_telecom', 33, 'payback90', 'Indicador de repago a 90 días; excluido del modelo base', false),
    ('delinquency_telecom', 34, 'pcircle', 'Círculo telecom; constante en la fuente', false),
    ('delinquency_telecom', 35, 'pdate', 'Fecha de la operación', false)
on conflict (source_name, column_name) do update set
    ordinal_position = excluded.ordinal_position,
    business_description = excluded.business_description,
    is_target = excluded.is_target;
