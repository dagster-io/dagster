"""✅ Multi-Partition Solution - Fixes GitHub Issue #28915.

Core Idea: Separate assets, share logic, avoid partition definition conflicts
"""

from dagster import Definitions

# Import recommended solution
from simple_multi_partition_solution import (
    daily_updates_job,
    data_record_daily_updates,
    data_record_monthly_backfill,
    monthly_backfill_job,
)

# Definitions
defs = Definitions(
    assets=[
        data_record_daily_updates,    # Daily incremental updates
        data_record_monthly_backfill, # Monthly full backfill
    ],
    jobs=[
        daily_updates_job,
        monthly_backfill_job,
    ]
)


