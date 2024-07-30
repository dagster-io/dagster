from typing import Any, Mapping, Sequence, cast

from dagster import asset, define_asset_job
from dagster._core.definitions.cacheable_assets import (
    CACHED_ASSET_ID_KEY,
    CACHED_ASSET_METADATA_KEY,
    extract_from_current_repository_load_data,
)
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.repository_definition.repository_definition import (
    PendingRepositoryDefinition,
)
from dagster._core.execution.plan.external_step import local_external_step_launcher
from dagster._core.instance import DagsterInstance

FETCHED_KVS_KEY = "fetched_external_data"
USED_CACHE_KVS_KEY = "used_cached_external_data"

instance = DagsterInstance.get()
metadata_value_cached_assets: Sequence[Mapping[Any, Any]] | None = (
    extract_from_current_repository_load_data("my_cached_asset_id")
)

if metadata_value_cached_assets is not None:
    get_definitions_called = int(
        instance.run_storage.get_cursor_values({USED_CACHE_KVS_KEY}).get(USED_CACHE_KVS_KEY, "0")
    )
    instance.run_storage.set_cursor_values({USED_CACHE_KVS_KEY: str(get_definitions_called + 1)})
else:
    get_definitions_called = int(
        instance.run_storage.get_cursor_values({FETCHED_KVS_KEY}).get(FETCHED_KVS_KEY, "0")
    )
    instance.run_storage.set_cursor_values({FETCHED_KVS_KEY: str(get_definitions_called + 1)})

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


pending_repo_from_cached_asset_metadata = cast(
    PendingRepositoryDefinition,
    Definitions(
        assets=[cached_asset, other_cached_asset],
        jobs=[define_asset_job("all_asset_job")],
    ).get_inner_repository(),
)

pending_repo_from_cached_asset_metadata_with_step_launcher = cast(
    PendingRepositoryDefinition,
    Definitions(
        assets=[cached_asset, other_cached_asset],
        jobs=[define_asset_job("all_asset_job")],
        resources={"step_launcher": local_external_step_launcher},
    ).get_inner_repository(),
)
