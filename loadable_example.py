from typing import List, Mapping, Sequence, Union

from dagster import _check as check
from dagster._core.definitions.asset_key import AssetKey
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.decorators.asset_decorator import asset, multi_asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.loadable import (
    AssetSpecRecord,
    DefLoadingContext,
    DefsRecord,
    LoadableCacheableAssetsDefinitionAdapter,
    LoadableDefs,
    load_defs,
)
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
)
from dagster._core.instance import DagsterInstance


def fetch_table_names_from_rest_api() -> List[str]:
    return ["lakehouse_a"]


class LakehouseDefs(LoadableDefs):
    def __init__(self) -> None:
        super().__init__(external_source_key="lakehouse_api")

    def compute_defs_record(self, context: DefLoadingContext) -> DefsRecord:
        return DefsRecord(
            asset_spec_records=[
                AssetSpecRecord(key=AssetKey(table_name))
                for table_name in fetch_table_names_from_rest_api()
            ]
        )

    def definitions_from_record(self, defs_record: DefsRecord) -> Definitions:
        @multi_asset(specs=defs_record.to_asset_specs())
        def an_asset() -> None: ...

        return Definitions(assets=[an_asset])


@asset
def another_asset() -> None: ...


def loadable_legacy_system_defs() -> LoadableDefs:
    # imagine you had an existing class LegacySystemCacheableAssetsDefinition
    # that you did not want to modify
    class LegacySystemCacheableAssetsDefinition(CacheableAssetsDefinition):
        def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
            return [AssetsDefinitionCacheableData(extra_metadata={"value": "legacy_a"})]

        def build_definitions(
            self, data: Sequence[AssetsDefinitionCacheableData]
        ) -> Sequence[AssetsDefinition]:
            value = (
                check.inst(next(iter(data)), AssetsDefinitionCacheableData).extra_metadata or {}
            )["value"]

            @asset(name=value)
            def an_asset() -> None: ...

            return [an_asset]

    # Here is how you would adapt it:
    return LoadableCacheableAssetsDefinitionAdapter(
        LegacySystemCacheableAssetsDefinition("ksjdkfsjdklfjslkdjf")
    )


daily_partitions_def = DailyPartitionsDefinition(start_date="2021-01-01")


class HardedPartitionedDefs(LoadableDefs):
    def __init__(self) -> None:
        super().__init__(external_source_key="partitioned_api")

    def compute_defs_record(self, context: DefLoadingContext) -> DefsRecord:
        return DefsRecord(
            asset_spec_records=[AssetSpecRecord(key=AssetKey("some_partitioned_table"))]
        )

    def definitions_from_record(self, defs_record: DefsRecord) -> Definitions:
        @multi_asset(specs=defs_record.to_asset_specs(partitions_def=daily_partitions_def))
        def blah_blah_blah() -> None: ...

        return Definitions(assets=[blah_blah_blah])


hourly_partition_def = HourlyPartitionsDefinition(start_date="2021-01-01-01:00")


class PartitioningDeterminedByAPI(LoadableDefs):
    def __init__(self) -> None:
        super().__init__(external_source_key="partitioning_api_2")

    def compute_defs_record(self, context: DefLoadingContext) -> DefsRecord:
        # imagine the string "hourly" or "daily" was returned by the API
        # but you want the source of truth for all partitiong to be in Python
        return DefsRecord(
            asset_spec_records=[
                AssetSpecRecord(
                    key=AssetKey("some_partitioned_table_1"), metadata={"partitioning": "hourly"}
                ),
                AssetSpecRecord(
                    key=AssetKey("some_partitioned_table_2"), metadata={"partitioning": "daily"}
                ),
            ]
        )

    def definitions_from_record(self, defs_record: DefsRecord) -> Definitions:
        def _apply_partitioning(spec: AssetSpec) -> AssetSpec:
            if spec.metadata.get("partitioning") == "hourly":
                return spec._replace(partitions_def=hourly_partition_def)
            elif spec.metadata.get("partitioning") == "daily":
                return spec._replace(partitions_def=daily_partitions_def)
            else:
                return spec

        @multi_asset(
            specs=[
                _apply_partitioning(spec)
                for spec in defs_record.to_asset_specs(partitions_def=daily_partitions_def)
            ]
        )
        def blah_blah_blah() -> None: ...

        return Definitions(assets=[blah_blah_blah])


# we can make context optional
def defs(context: DefLoadingContext) -> Definitions:
    # This is now a vanilla definitions object.
    legacy_system_defs = loadable_legacy_system_defs().load(context)
    # so here you could do things like build derived asset checks from them
    lake_house_defs = LakehouseDefs().load(context)

    return Definitions.merge(
        Definitions(assets=[another_asset]),
        legacy_system_defs,
        lake_house_defs,
        HardedPartitionedDefs().load(context),
    )


def defs_using_helper(context: DefLoadingContext) -> Definitions:
    # convienence function to load all the defs and merge them
    # Definitions.load_all(...)
    return load_all(
        context,
        loadable_legacy_system_defs(),
        LakehouseDefs(),
        HardedPartitionedDefs(),
        Definitions(assets=[another_asset]),
    )


def load_all(context: DefLoadingContext, *defs: Union[LoadableDefs, Definitions]) -> Definitions:
    return Definitions.merge(*[d.load(context) if isinstance(d, LoadableDefs) else d for d in defs])


if __name__ == "__main__":
    # how you would call in tests
    assert isinstance(load_defs(defs), Definitions)

    instance = DagsterInstance.get()
    # save the definitions to the instance
    assert isinstance(
        defs(DefLoadingContext(load_from_storage=False, instance=instance)), Definitions
    )

    # load from storage
    assert isinstance(
        defs(DefLoadingContext(load_from_storage=True, instance=instance)), Definitions
    )

    def _raise() -> Mapping[str, str]:
        raise Exception("should not be called")

    # make storage load fail
    instance.run_storage.get_cursor_values = lambda *args, **kwargs: _raise()

    # doesn't touch storage
    assert isinstance(
        defs(DefLoadingContext(load_from_storage=False, instance=instance)), Definitions
    )

    # does touch storage, fails
    caught = False
    try:
        assert isinstance(
            defs(DefLoadingContext(load_from_storage=True, instance=instance)), Definitions
        )
    except Exception as e:
        caught = True
        assert "should not be called" in str(e)

    assert caught
