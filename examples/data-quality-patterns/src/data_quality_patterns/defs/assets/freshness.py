"""Freshness policies for timeliness dimension.

Freshness policies ensure data is up-to-date and available when needed.
This is the Timeliness dimension of data quality.

FreshnessPolicy automatically creates checks that verify assets are
materialized within the expected time window.
"""

from datetime import timedelta

import dagster as dg

# Create a freshness policy for assets that should be updated daily
daily_freshness_policy = dg.FreshnessPolicy.time_window(
    fail_window=timedelta(hours=24),
    warn_window=timedelta(hours=12),
)

# Create a freshness policy for assets that should be updated hourly
hourly_freshness_policy = dg.FreshnessPolicy.time_window(
    fail_window=timedelta(hours=2),
    warn_window=timedelta(hours=1),
)
