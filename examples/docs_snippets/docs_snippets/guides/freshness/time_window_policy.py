from datetime import timedelta

from dagster import FreshnessPolicy

# Create a freshness policy that requires a materialization at least once every 24 hours,
# and warns if the latest materialization is older than 12 hours.
policy = FreshnessPolicy.time_window(
    fail_window=timedelta(hours=24), warn_window=timedelta(hours=12)
)
