/*
EDRSS V2 — Calidad y observabilidad
Objetivo : revisar en una consulta el estado de cada lote y sus controles.
Entradas : Bronze, Silver y Gold.
Salidas  : gold.pipeline_status, api.page_data_quality.
*/

create or replace view gold.pipeline_status
with (security_invoker = true)
as
select
    b.batch_id,
    b.source_file_name,
    b.source_file_hash,
    b.status as ingestion_status,
    b.loaded_row_count,
    b.rejected_row_count,
    b.started_at,
    b.completed_at,
    count(distinct s.operation_sk) as silver_rows,
    count(distinct g.operation_sk) as gold_rows
from bronze.ingestion_batch b
left join silver.telecom_operations s using (batch_id)
left join gold.ml_features g using (batch_id, operation_sk)
group by
    b.batch_id, b.source_file_name, b.source_file_hash, b.status,
    b.loaded_row_count, b.rejected_row_count, b.started_at, b.completed_at;

create or replace view api.page_data_quality
with (security_invoker = true)
as
select
    q.batch_id,
    q.layer_name,
    q.check_name,
    q.status,
    q.observed_value,
    q.expected_value,
    q.details,
    q.checked_at
from silver.data_quality_result q;

grant select on all tables in schema api to authenticated, service_role;

