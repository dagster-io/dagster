from abc import ABC, abstractmethod
from typing import AbstractSet, Dict, Generic, Iterable, Mapping, Optional, Sequence, Set, TypeVar

from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.events.log import EventLogEntry
from dagster._core.instance import DagsterInstance
from dagster._core.storage.asset_check_execution_record import AssetCheckExecutionRecord
from dagster._core.storage.dagster_run import DagsterRun, RunsFilter
from dagster._core.storage.event_log.base import AssetRecord

K = TypeVar("K")
V = TypeVar("V")


class BatchInstanceLoader(Generic[K, V], ABC):
    """Generic base class for fetching data from a DagsterInstance in batches."""

    _cache: Dict[K, Optional[V]]
    _unfetched_keys: Set[K]
    _instance: DagsterInstance

    def __init__(self, instance: DagsterInstance, *, initial_keys: Optional[Iterable[K]] = None):
        self._cache = {}
        self._unfetched_keys = set(initial_keys or [])
        self._instance = instance

    def clear_cache(self) -> None:
        self._cache = {}

    def add_keys(self, keys: Iterable[K]) -> None:
        self._unfetched_keys = self._unfetched_keys.union(set(keys).difference(self._cache.keys()))

    def fetch(self) -> None:
        if not self._unfetched_keys:
            return
        results = self._query(self._unfetched_keys)
        self._cache = {**self._cache, **{k: results.get(k) for k in self._unfetched_keys}}
        self._unfetched_keys = set()

    def get_multiple(self, keys: Iterable[K]) -> Mapping[K, Optional[V]]:
        self.add_keys(keys)
        self.fetch()
        return {k: self._cache[k] for k in keys}

    def get(self, key: K) -> Optional[V]:
        return self.get_multiple([key])[key]

    def get_values(self, keys: Iterable[K]) -> Sequence[V]:
        return [v for v in self.get_multiple(keys).values() if v is not None]

    def has(self, key: K) -> bool:
        return key in self._cache

    @abstractmethod
    def _query(self, keys: Set[K]) -> Mapping[K, V]: ...


class BatchRunLoader(BatchInstanceLoader[str, DagsterRun]):
    def _query(self, keys: AbstractSet[str]) -> Mapping[str, DagsterRun]:
        runs = self._instance.get_runs(filters=RunsFilter(run_ids=list(keys)))
        return {run.run_id: run for run in runs}


class BatchAssetRecordLoader(BatchInstanceLoader[AssetKey, AssetRecord]):
    def _query(self, keys: AbstractSet[AssetKey]) -> Mapping[AssetKey, AssetRecord]:
        records = self._instance.get_asset_records(asset_keys=list(keys))
        return {record.asset_entry.asset_key: record for record in records}

    def get_latest_materialization(self, key: AssetKey) -> Optional[EventLogEntry]:
        record = self.get(key)
        return record.asset_entry.last_materialization if record else None

    def get_latest_observation(self, key: AssetKey) -> Optional[EventLogEntry]:
        record = self.get(key)
        return record.asset_entry.last_observation if record else None


class BatchAssetCheckRecordLoader(BatchInstanceLoader[AssetCheckKey, AssetCheckExecutionRecord]):
    def _query(
        self, keys: AbstractSet[AssetCheckKey]
    ) -> Mapping[AssetCheckKey, AssetCheckExecutionRecord]:
        return self._instance.event_log_storage.get_latest_asset_check_execution_by_key(list(keys))
