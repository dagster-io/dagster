from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Mapping, Optional, Sequence, Union

from dagster._core.definitions.asset_dep import AssetDep
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._record import record
from dagster._serdes.serdes import deserialize_value, serialize_value, whitelist_for_serdes

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance


@whitelist_for_serdes
@record
class AssetDepRecord:
    asset_key: AssetKey
    # todo partition mapping


@whitelist_for_serdes
@record
class AssetSpecRecord:
    key: AssetKey
    description: Optional[str] = None
    metadata: Optional[Mapping[str, Any]] = None
    deps: Optional[Sequence[AssetDepRecord]] = None
    tags: Optional[Mapping[str, str]] = None
    group_name: Optional[str] = None


@whitelist_for_serdes
@record
class AssetCheckSpecRecord:
    key: AssetCheckKey


def record_to_asset_spec(asr: AssetSpecRecord) -> AssetSpec:
    return AssetSpec(
        key=asr.key,
        metadata=asr.metadata,
        description=asr.description,
        tags=asr.tags,
        deps=[AssetDep(apr.asset_key) for apr in (asr.deps or [])],
        group_name=asr.group_name,
    )


@whitelist_for_serdes
@record
class DefsRecord:
    asset_spec_records: Optional[Sequence[AssetSpecRecord]] = None
    # asset_check_specs: Optional[Sequence[AssetCheckSpec]] = None
    # for backwards compat and weird shit
    extra: Any = None

    # TODO eliminate additional values
    def to_asset_specs(self, **additional_values) -> Sequence[AssetSpec]:
        return [
            record_to_asset_spec(asr)._replace(**additional_values)
            for asr in (self.asset_spec_records or [])
        ]


@dataclass
class DefLoadingContext:
    load_from_storage: bool
    instance: "DagsterInstance"


@dataclass
class DefinitionsFnWrapper:
    def_fn: Callable


def fetch_defs_record(instance: "DagsterInstance", key: str) -> Optional[DefsRecord]:
    str_value = instance.run_storage.get_cursor_values({key}).get(key)
    if not str_value:
        return None
    return deserialize_value(str_value, as_type=DefsRecord)


def store_defs_record(instance: "DagsterInstance", key: str, defs_record: DefsRecord) -> None:
    serialized = serialize_value(defs_record)
    return instance.run_storage.set_cursor_values({key: serialized})


class LoadableDefs(ABC):
    def __init__(self, external_source_key: str):
        self.external_source_key = external_source_key

    # This invokes against potentially unreliable APIS, like an API call. Or potentially slow APIs, like a dbt manifest parse.
    # We could also add new APIs/UI that invokes this without a full code server reload
    @abstractmethod
    def compute_defs_record(self, context: DefLoadingContext) -> DefsRecord: ...

    @abstractmethod
    def definitions_from_record(self, defs_record: DefsRecord) -> Definitions: ...

    def load(self, context: DefLoadingContext) -> Definitions:
        # The system will set load_from_storage to true in cases like run worker loads
        if context.load_from_storage:
            defs_record = fetch_defs_record(context.instance, self._get_key())
            if not defs_record:
                raise Exception(f"Could not load defs record for {self._get_key()}")
            return self.definitions_from_record(defs_record)

        defs_record = self.compute_defs_record(context)
        definitions = self.definitions_from_record(defs_record)

        store_defs_record(context.instance, self._get_key(), defs_record)

        # only return if successfully stored
        return definitions

    def sync_load(self, instance: Optional["DagsterInstance"] = None) -> Definitions:
        from dagster._core.instance import DagsterInstance
        return self.load(DefLoadingContext(load_from_storage=False, instance=instance or DagsterInstance.get()))

    # This is a problematic bit. Probably should construct from context with repo and location name etc.
    def _get_key(self) -> str:
        return f"loadable_defs/{self.external_source_key}"


class LoadableCacheableAssetsDefinitionAdapter(LoadableDefs):
    def __init__(self, cacheable_assets_def: CacheableAssetsDefinition):
        self.cacheable_assets_def = cacheable_assets_def
        super().__init__(external_source_key=self.cacheable_assets_def.unique_id)

    def compute_defs_record(self, context: DefLoadingContext) -> DefsRecord:
        datas = self.cacheable_assets_def.compute_cacheable_data()
        return DefsRecord(extra=datas)

    def definitions_from_record(self, defs_record: DefsRecord) -> Definitions:
        assets_defs = self.cacheable_assets_def.build_definitions(defs_record.extra)
        return Definitions(assets=assets_defs)


def load_defs(
    defs_fn: Callable[[DefLoadingContext], Definitions],
    instance: Optional["DagsterInstance"] = None,
) -> Definitions:
    from dagster._core.instance import DagsterInstance

    instance = instance or DagsterInstance.get()
    return defs_fn(DefLoadingContext(load_from_storage=False, instance=instance))

def load_all_defs(context: DefLoadingContext, *defs: Union[LoadableDefs, Definitions]) -> Definitions:
    return Definitions.merge(*[d.load(context) if isinstance(d, LoadableDefs) else d for d in defs])
