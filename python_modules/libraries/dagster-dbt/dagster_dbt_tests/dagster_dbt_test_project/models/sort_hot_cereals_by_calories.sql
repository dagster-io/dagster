{{ config(tags=["bar"], dagster_freshness_policy={"maximum_lag_minutes": 123}) }}
SELECT *
FROM {{ ref('sort_by_calories') }}
WHERE type='H'