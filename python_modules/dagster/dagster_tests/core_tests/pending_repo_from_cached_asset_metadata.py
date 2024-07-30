from typing import Any, Mapping, Sequence

from dagster import asset, define_asset_job, repository
from dagster._core.definitions.cacheable_assets import (
    CACHED_ASSET_ID_KEY,
    CACHED_ASSET_METADATA_KEY,
    extract_from_current_repository_load_data,
)
from dagster._core.definitions.repository_definition.valid_definitions import (
    PendingRepositoryListDefinition,
)
from dagster._core.instance import DagsterInstance

metadata_value_cached_assets: Sequence[Mapping[Any, Any]] | None = (
    extract_from_current_repository_load_data("my_cached_asset_id")
)

if metadata_value_cached_assets is None:
    instance = DagsterInstance.get()
    kvs_key = "fetch_cached_data"
    get_definitions_called = int(
        instance.run_storage.get_cursor_values({kvs_key}).get(kvs_key, "0")
    )
    instance.run_storage.set_cursor_values({kvs_key: str(get_definitions_called + 1)})

    metadata_value_cached_assets = [{"foo": "bar"}, {"baz": "qux"}]

assert metadata_value_cached_assets == [
    {"foo": "bar"},
    {"baz": "qux"},
], metadata_value_cached_assets


@asset(
    metadata={
        CACHED_ASSET_ID_KEY: "my_cached_asset_id",
        CACHED_ASSET_METADATA_KEY: {"foo": "bar"},
    }
)
def cached_asset():
    return 5


@asset(
    metadata={
        CACHED_ASSET_ID_KEY: "my_cached_asset_id",
        CACHED_ASSET_METADATA_KEY: {"baz": "qux"},
    }
)
def other_cached_asset():
    return 10


@repository
def pending_repo_from_cached_asset_metadata() -> Sequence[PendingRepositoryListDefinition]:
    return [
        cached_asset,
        other_cached_asset,
        define_asset_job(
            "all_asset_job",
        ),
    ]
