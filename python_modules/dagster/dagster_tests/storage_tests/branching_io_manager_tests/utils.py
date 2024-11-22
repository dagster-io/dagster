from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from dagster import (
    AssetKey,
    DagsterInstance,
    Definitions,
    ExecuteInProcessResult,
    InputContext,
    IOManager,
    OutputContext,
)
from dagster._config.pythonic_config.io_manager import ConfigurableIOManager
from dagster._core.definitions.events import CoercibleToAssetKey
from dagster._core.event_api import EventLogRecord
from dagster._core.execution.context.init import InitResourceContext
from pydantic import PrivateAttr


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
        all_keys = list(self.defs.get_repository_def().asset_graph.get_all_asset_keys())
        job_def = self.defs.get_implicit_job_def_for_assets(all_keys)
        assert job_def
        return job_def.execute_in_process(instance=self.instance, partition_key=partition_key)

    def materialize_assets(
        self, asset_selection: Sequence[CoercibleToAssetKey], partition_key: Optional[str] = None
    ) -> ExecuteInProcessResult:
        asset_keys = [AssetKey.from_coercible(asset_key) for asset_key in asset_selection]
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

    def get_last_5000_asset_materialization_event_records(
        self, asset_key: CoercibleToAssetKey
    ) -> list[EventLogRecord]:
        return [
            *self.instance.fetch_materializations(
                AssetKey.from_coercible(asset_key), limit=5000
            ).records
        ]


class AssetBasedInMemoryIOManager(IOManager):
    """In memory I/O manager for testing asset-based jobs and workflows. Can handle both
    partitioned and unpartitioned assets.
    """

    def __init__(self):
        self.values = {}

    def handle_output(self, context: OutputContext, obj: Any):
        keys = self._keys_from_context(context)
        if keys is None:
            self.values[None] = obj
        else:
            for key in keys:
                self.values[key] = obj

    def load_input(self, context: InputContext) -> Any:
        keys = self._keys_from_context(context)
        if keys is None:
            return self.values[None]
        else:
            return (
                {key[-1]: self.values[key] for key in keys}
                if len(keys) > 1
                else self.values[keys[0]]
            )

    def has_value(
        self, asset_key: CoercibleToAssetKey, partition_key: Optional[str] = None
    ) -> bool:
        return self._get_key(AssetKey.from_coercible(asset_key), partition_key) in self.values

    def get_value(self, asset_key: CoercibleToAssetKey, partition_key: Optional[str] = None) -> Any:
        return self.values.get(self._get_key(AssetKey.from_coercible(asset_key), partition_key))

    def _keys_from_context(
        self, context: Union[InputContext, OutputContext]
    ) -> Optional[Sequence[tuple[str, ...]]]:
        if not context.has_asset_key:
            return None

        partition_keys = context.asset_partition_keys if context.has_asset_partitions else [None]
        return [self._get_key(context.asset_key, partition_key) for partition_key in partition_keys]

    def _get_key(self, asset_key: AssetKey, partition_key: Optional[str]) -> tuple:
        return tuple([*asset_key.path] + [partition_key] if partition_key is not None else [])


LOG = []


class ConfigurableAssetBasedInMemoryIOManager(ConfigurableIOManager):
    """ConfigurableResource version of the above. This is useful for testing
    that the config system is working correctly & to test the setup/teardown logic.
    """

    name: str
    _values: dict = PrivateAttr(default={})

    def setup_for_execution(self, context: InitResourceContext) -> None:
        self._values = {}
        LOG.append(f"setup_for_execution {self.name}")

    def teardown_after_execution(self, context: InitResourceContext) -> None:
        LOG.append(f"teardown_after_execution {self.name}")

    def handle_output(self, context: OutputContext, obj: Any):
        keys = self._keys_from_context(context)
        if keys is None:
            self._values[None] = obj
        else:
            for key in keys:
                self._values[key] = obj

    def load_input(self, context: InputContext) -> Any:
        keys = self._keys_from_context(context)
        if keys is None:
            return self.values[None]
        else:
            return (
                {key[-1]: self._values[key] for key in keys}
                if len(keys) > 1
                else self._values[keys[0]]
            )

    def has_value(
        self, asset_key: CoercibleToAssetKey, partition_key: Optional[str] = None
    ) -> bool:
        return self._get_key(AssetKey.from_coercible(asset_key), partition_key) in self._values

    def get_value(self, asset_key: CoercibleToAssetKey, partition_key: Optional[str] = None) -> Any:
        return self._values.get(self._get_key(AssetKey.from_coercible(asset_key), partition_key))

    def _keys_from_context(
        self, context: Union[InputContext, OutputContext]
    ) -> Optional[Sequence[tuple[str, ...]]]:
        if not context.has_asset_key:
            return None

        partition_keys = context.asset_partition_keys if context.has_asset_partitions else [None]
        return [self._get_key(context.asset_key, partition_key) for partition_key in partition_keys]

    def _get_key(self, asset_key: AssetKey, partition_key: Optional[str]) -> tuple:
        return tuple([*asset_key.path] + [partition_key] if partition_key is not None else [])
