
from dagster._record import record
from dagster_shared.serdes import whitelist_for_serdes


class FreshnessCondition:
    """Base class for all freshness conditions. This defines how freshness will be evaluated for a given entity."""
