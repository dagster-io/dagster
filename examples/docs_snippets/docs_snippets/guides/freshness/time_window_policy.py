from datetime import timedelta

from dagster._core.definitions.freshness import (
    InternalFreshnessPolicy,
    TimeWindowFreshnessPolicy,
)

# Create a policy that requires updates every 24 hours
policy = TimeWindowFreshnessPolicy.from_timedeltas(
    fail_window=timedelta(hours=24),
    warn_window=timedelta(hours=12),  # optional, must be less than fail_window
)

# Or, equivalently, from the base class
policy = InternalFreshnessPolicy.time_window(
    fail_window=timedelta(hours=24), warn_window=timedelta(hours=12)
)
