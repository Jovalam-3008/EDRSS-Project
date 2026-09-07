/*
EDRSS V2 — Preparación de la base
Objetivo : crear los esquemas y funciones comunes de conversión segura.
Entradas : ninguna.
Salidas  : bronze, silver, gold, api y funciones auxiliares de Silver.
Ejecución: primera; puede repetirse sin eliminar datos.
*/
create schema if not exists bronze;
create schema if not exists silver;
create schema if not exists gold;
create schema if not exists api;

comment on schema bronze is 'EDRSS - datos fuente inmutables y trazabilidad de ingesta';
comment on schema silver is 'EDRSS - datos tipificados, validados y variables determinísticas';
comment on schema gold is 'EDRSS - consumibles certificados para ML, KPI y scoring';
comment on schema api is 'EDRSS - superficie mínima y controlada para dashboard';

create or replace function silver.try_double(value text)
returns double precision
language plpgsql
immutable
as $$
begin
    if value is null or btrim(value) = '' then return null; end if;
    return value::double precision;
exception when others then
    return null;
end;
$$;

create or replace function silver.try_smallint(value text)
returns smallint
language plpgsql
immutable
as $$
begin
    if value is null or btrim(value) = '' then return null; end if;
    return value::smallint;
exception when others then
    return null;
end;
$$;

create or replace function silver.try_date_dmy(value text)
returns date
language plpgsql
immutable
as $$
begin
    if value is null or btrim(value) = '' then return null; end if;
    return to_date(value, 'DD-MM-YYYY');
exception when others then
    return null;
end;
$$;

create or replace function silver.safe_divide(
    numerator double precision,
    denominator double precision
)
returns double precision
language sql
immutable
as $$
    select numerator / nullif(denominator, 0.0)
$$;
