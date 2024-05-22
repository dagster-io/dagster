from typing import TYPE_CHECKING, Iterable, Mapping, Optional, Sequence, Set

import dagster._check as check
from dagster._core.definitions.events import AssetKey
from dagster._core.events.log import EventLogEntry
from dagster._core.instance import DagsterInstance

if TYPE_CHECKING:
    from dagster._core.storage.event_log.base import AssetSummaryRecord


class AssetSummaryRecordLoader:
    """A batch loader that fetches asset records.  This loader is expected to be
    instantiated with a set of asset keys.
    """

    def __init__(self, instance: DagsterInstance, asset_keys: Iterable[AssetKey]):
        self._instance = instance
        self._unfetched_asset_keys: Set[AssetKey] = set(asset_keys)
        self._asset_summary_records: Mapping[AssetKey, Optional["AssetSummaryRecord"]] = {}

    def add_asset_keys(self, asset_keys: Iterable[AssetKey]):
        unfetched_asset_keys = set(asset_keys).difference(self._asset_summary_records)
        self._unfetched_asset_keys = self._unfetched_asset_keys.union(unfetched_asset_keys)

    def get_asset_summary_record(self, asset_key: AssetKey) -> Optional["AssetSummaryRecord"]:
        if (
            asset_key not in self._asset_summary_records
            and asset_key not in self._unfetched_asset_keys
        ):
            check.failed(
                f"Asset key {asset_key} not recognized for this loader. Expected one of:"
                f" {self._unfetched_asset_keys.union(self._asset_summary_records.keys())}"
            )

        if asset_key in self._unfetched_asset_keys:
            self.fetch()

        return self._asset_summary_records.get(asset_key)

    def clear_cache(self) -> None:
        """For use in tests."""
        self._unfetched_asset_keys = self._unfetched_asset_keys.union(self._asset_records.keys())
        self._asset_records = {}

    def has_cached_asset_summary_record(self, asset_key: AssetKey):
        return asset_key in self._asset_summary_records

    def get_asset_summary_records(
        self, asset_keys: Sequence[AssetKey]
    ) -> Sequence["AssetSummaryRecord"]:
        records = [self.get_asset_summary_record(asset_key) for asset_key in asset_keys]
        return [record for record in records if record]

    def get_latest_materialization_for_asset_key(
        self, asset_key: AssetKey
    ) -> Optional[EventLogEntry]:
        asset_record = self.get_asset_summary_record(asset_key)
        if not asset_record:
            return None

        return asset_record.asset_entry.last_materialization

    def get_latest_observation_for_asset_key(self, asset_key: AssetKey) -> Optional[EventLogEntry]:
        check.invariant(
            self._instance.event_log_storage.asset_records_have_last_observation,
            "Event log storage must support fetching the last observation from asset records",
        )

        asset_summary_record = self.get_asset_summary_record(asset_key)
        if not asset_summary_record:
            return None

        return asset_summary_record.asset_entry.last_observation

    def fetch(self) -> None:
        if not self._unfetched_asset_keys:
            return

        new_records = {
            record.asset_entry.asset_key: record
            for record in self._instance.get_asset_records(list(self._unfetched_asset_keys))
        }

        self._asset_summary_records = {
            **self._asset_summary_records,
            **{asset_key: new_records.get(asset_key) for asset_key in self._unfetched_asset_keys},
        }
        self._unfetched_asset_keys = set()
