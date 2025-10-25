from datetime import timedelta

from dagster import FreshnessPolicy, asset


@asset(
    freshness_policy=FreshnessPolicy.cron(
        deadline_cron="0 10 * * *",
        lower_bound_delta=timedelta(hours=1),
        timezone="America/Los_Angeles",
    )
)
def daily_asset():
    """Expected to materialize every day between 9:00am and 10:00am Pacific Time.

    If the asset materializes between 9am and 10am, it is fresh, and will remain fresh until at least the next deadline (10am the next day).

    If the asset has not materialized by 10am, it fails the freshness policy. It will remain in the fail state until it materializes again.
    Once it materializes, it will become fresh and remain fresh until at least the next deadline (10am the next day).

    """
    pass
