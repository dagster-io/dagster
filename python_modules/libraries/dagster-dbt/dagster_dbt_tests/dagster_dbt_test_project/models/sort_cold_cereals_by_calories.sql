{{ config(tags=["foo"], schema="cold_schema") }}
SELECT *
FROM {{ ref('sort_by_calories') }}
WHERE type='C'