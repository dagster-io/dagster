{{ config(tags=["foo"], schema="cold_schema") }}
SELECT *
FROM {{ ref('ephem2') }}
WHERE type='C'