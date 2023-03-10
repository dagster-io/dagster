from contextlib import contextmanager
from typing import Any, List, Optional, Sequence, Union

from dagster import (
    AssetKey,
    DagsterInstance,
    Definitions,
    ExecuteInProcessResult,
    InputContext,
    IOManager,
    OutputContext,
)
from dagster._core.definitions.events import CoercibleToAssetKey
from dagster._core.event_api import EventLogRecord, EventRecordsFilter
from dagster._core.events import DagsterEventType


class DefinitionsRunner:
    """Helper class for running asset-oriented tests. Handles threading
    through the instance for you (this is easy to forget to do).
    """

    def __init__(self, defs: Definitions, instance: DagsterInstance):
        self.defs = defs
        self.instance = instance

    @staticmethod
    @contextmanager
    def ephemeral(defs: Definitions):
        with DagsterInstance.ephemeral() as instance:
            yield DefinitionsRunner(defs, instance)

    def materialize_all_assets(self, partition_key: Optional[str] = None) -> ExecuteInProcessResult:
        all_keys = list(
            self.defs.get_repository_def()._assets_defs_by_key.keys()  # pylint: disable=protected-access
        )
        job_def = self.defs.get_implicit_job_def_for_assets(all_keys)
        assert job_def
        return job_def.execute_in_process(instance=self.instance, partition_key=partition_key)

    def materialize_assets(
        self, asset_selection: Sequence[CoercibleToAssetKey], partition_key: Optional[str] = None
    ) -> ExecuteInProcessResult:
        asset_keys = [AssetKey.from_coerceable(asset_key) for asset_key in asset_selection]
        job_def = self.defs.get_implicit_job_def_for_assets(asset_keys)
        assert job_def
        return job_def.execute_in_process(
            instance=self.instance,
            asset_selection=asset_keys,
            partition_key=partition_key,
        )

    def materialize_asset(
        self, asset_key: CoercibleToAssetKey, partition_key: Optional[str] = None
    ) -> ExecuteInProcessResult:
        return self.materialize_assets([asset_key], partition_key)

    def load_asset_value(
        self, asset_key: CoercibleToAssetKey, partition_key: Optional[str] = None
    ) -> object:
        return self.defs.load_asset_value(
            asset_key=asset_key, instance=self.instance, partition_key=partition_key
        )

    def get_all_asset_materialization_event_records(
        self, asset_key: CoercibleToAssetKey
    ) -> List[EventLogRecord]:
        return [
            *self.instance.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=AssetKey.from_coerceable(asset_key),
                )
            )
        ]


class AssetBasedInMemoryIOManager(IOManager):
    """In memory I/O manager for testing asset-based jobs and workflows. Can handle both
    partitioned and unpartitioned assets.
    """

    def __init__(self):
        self.values = {}

    def handle_output(self, context: OutputContext, obj: Any):
        key = self._key_from_context(context)
        self.values[key] = obj

    def load_input(self, context: InputContext) -> Any:
        key = self._key_from_context(context)
        return self.values[key]

    def has_value(
        self, asset_key: CoercibleToAssetKey, partition_key: Optional[str] = None
    ) -> bool:
        return self._get_key(AssetKey.from_coerceable(asset_key), partition_key) in self.values

    def get_value(self, asset_key: CoercibleToAssetKey, partition_key: Optional[str] = None) -> Any:
        return self.values.get(self._get_key(AssetKey.from_coerceable(asset_key), partition_key))

    def _key_from_context(self, context: Union[InputContext, OutputContext]):
        return self._get_key(
            context.asset_key, context.partition_key if context.has_partition_key else None
        )

    def _get_key(self, asset_key: AssetKey, partition_key: Optional[str]) -> tuple:
        return tuple([*asset_key.path] + [partition_key] if partition_key is not None else [])
