{{ config(
        tags=["foo"],
        schema="cold_schema",
        dagster_freshness_policy={
                "maximum_lag_minutes": 123,
                "cron_schedule": "0 9 * * *",
                "cron_schedule_timezone": "America/New_York",
        })
}}
SELECT *
FROM {{ ref('ephem2') }}
WHERE type='C'