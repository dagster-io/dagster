import datetime
from typing import NamedTuple, Optional

from dagster._annotations import experimental
from dagster._serdes.serdes import whitelist_for_serdes


@experimental
@whitelist_for_serdes
class AutoMaterializePolicy(NamedTuple):
    """An AutoMaterializePolicy specifies how Dagster should attempt to keep an asset up-to-date.

    There are two main modes of reconciliation: eager and lazy.

    Regardless of this selection an asset / partition will never be materialized if any of its
    parents are missing.

    For eager reconciliation, an asset / partition will be (re)materialized when:

    - it is missing
    - it or any of its children have a FreshnessPolicy that require more up-to-date data than it
      currently has
    - any of its parent assets / partitions have been updated more recently than it has

    For lazy reconciliation, an asset / partition will be (re)materialized when:

    - it is missing
    - it or any of its children have a FreshnessPolicy that require more up-to-date data than it
      currently has

    In essence, an asset with eager reconciliation will always incorporate the most up-to-date
    version of its parents, while an asset with lazy reconciliation will only update when necessary
    in order to stay in line with the relevant FreshnessPolicies.

    **Warning:**

    Constructing an AutoMaterializePolicy directly is not recommended as the API is subject to change.
    AutoMaterializePolicy.eager() and AutoMaterializePolicy.lazy() are the recommended API.
    """

    on_missing: bool
    on_upstream_data_newer: bool
    for_freshness: bool
    time_window_partition_scope_minutes: Optional[float]

    @property
    def time_window_partition_scope(self) -> Optional[datetime.timedelta]:
        if self.time_window_partition_scope_minutes is None:
            return None
        return datetime.timedelta(minutes=self.time_window_partition_scope_minutes)

    @staticmethod
    def eager() -> "AutoMaterializePolicy":
        return AutoMaterializePolicy(
            on_missing=True,
            on_upstream_data_newer=True,
            for_freshness=True,
            time_window_partition_scope_minutes=datetime.timedelta.resolution.total_seconds() / 60,
        )

    @staticmethod
    def lazy() -> "AutoMaterializePolicy":
        return AutoMaterializePolicy(
            on_missing=True,
            on_upstream_data_newer=False,
            for_freshness=True,
            time_window_partition_scope_minutes=datetime.timedelta.resolution.total_seconds() / 60,
        )
