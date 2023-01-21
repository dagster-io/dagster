{{ config(
        tags=["foo"],
        schema="cold_schema",
        dagster_freshness_policy={
                "maximum_lag_minutes": 123,
                "cron_schedule": "0 9 * * *"
        })
}}
SELECT *
FROM {{ ref('ephem2') }}
WHERE type='C'