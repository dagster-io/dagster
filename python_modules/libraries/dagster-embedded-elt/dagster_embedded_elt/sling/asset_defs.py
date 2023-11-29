import re
import uuid
<<<<<<< HEAD
from typing import Any, Dict, Generator, List, Optional, Union
=======
from typing import Any, Dict, List, Optional, Union
>>>>>>> cb080be97a (refactored to pass multiple streams into a builder to parallelize replication)

from dagster import (
    AssetExecutionContext,
    AssetsDefinition,
    AssetSpec,
    MaterializeResult,
    multi_asset,
)
from dagster._annotations import experimental

from dagster_embedded_elt.sling.resources import (
    SlingConnectionResource,
    SlingMode,
    SlingResource,
    SlingStreamReplicator,
)


@experimental
def build_sling_asset(
    asset_spec: AssetSpec,
    source_stream: str,
    target_object: str,
    mode: SlingMode = SlingMode.FULL_REFRESH,
    primary_key: Optional[Union[str, List[str]]] = None,
    update_key: Optional[str] = None,
    source_options: Optional[Dict[str, Any]] = None,
    target_options: Optional[Dict[str, Any]] = None,
    sling_resource_key: str = "sling",
) -> AssetsDefinition:
    """Asset Factory for using Sling to sync data from a source stream to a target object.

    Args:
        asset_spec (AssetSpec): The AssetSpec to use to materialize this asset.
        source_stream (str): The source stream to sync from. This can be a table, a query, or a path.
        target_object (str): The target object to sync to. This can be a table, or a path.
        mode (SlingMode, optional): The sync mode to use when syncing. Defaults to SlingMode.FULL_REFRESH.
        primary_key (Optional[Union[str, List[str]]], optional): The optional primary key to use when syncing.
        update_key (Optional[str], optional): The optional update key to use when syncing.
        source_options (Optional[Dict[str, Any]], optional): Any optional Sling source options to use when syncing.
        target_options (Optional[Dict[str, Any]], optional): Any optional target options to use when syncing.
        sling_resource_key (str, optional): The resource key for the SlingResource. Defaults to "sling".

    Examples:
        Creating a Sling asset that syncs from a file to a table:

        .. code-block:: python

            asset_spec = AssetSpec(key=["main", "dest_tbl"])
            asset_def = build_sling_asset(
                    asset_spec=asset_spec,
                    source_stream="file:///tmp/test.csv",
                    target_object="main.dest_table",
                    mode=SlingMode.INCREMENTAL,
                    primary_key="id"
            )

        Creating a Sling asset that syncs from a table to a file with a full refresh:

        .. code-block:: python

            asset_spec = AssetSpec(key="test.csv")
            asset_def = build_sling_asset(
                    asset_spec=asset_spec,
                    source_stream="main.dest_table",
                    target_object="file:///tmp/test.csv",
                    mode=SlingMode.FULL_REFRESH
            )


    """
    if primary_key is not None and not isinstance(primary_key, list):
        primary_key = [primary_key]

    @multi_asset(
        name=asset_spec.key.to_python_identifier(),
        compute_kind="sling",
        specs=[asset_spec],
        required_resource_keys={sling_resource_key},
    )
    def sync(context: AssetExecutionContext) -> MaterializeResult:
        sling: SlingResource = getattr(context.resources, sling_resource_key)
        last_row_count_observed = None
        for stdout_line in sling.sync(
            source_stream=source_stream,
            target_object=target_object,
            mode=mode,
            primary_key=primary_key,
            update_key=update_key,
            source_options=source_options,
            target_options=target_options,
        ):
            match = re.search(r"(\d+) rows", stdout_line)
            if match:
                last_row_count_observed = int(match.group(1))
            context.log.info(stdout_line)

        return MaterializeResult(
            metadata=(
                {} if last_row_count_observed is None else {"row_count": last_row_count_observed}
            )
        )

    return sync


@experimental
def build_assets_from_sling_streams(
    source: SlingConnectionResource,
    target: SlingConnectionResource,
    streams: List[Dict[str, Any]],
    mode: SlingMode = SlingMode.FULL_REFRESH,
    target_object: str = "{target_schema}.{stream_schema}_{stream_table}",
    source_options: Optional[Dict[str, Any]] = None,
    target_options: Optional[Dict[str, Any]] = None,
) -> AssetsDefinition:
<<<<<<< HEAD
=======
    """Asset Factory for using Sling to sync data from a source stream to a target object.

    Args:
        source (SlingConnectionResource): The source SlingConnectionResource to use.
        target (SlingConnectionResource): The target SlingConnectionResource to use.
        stream (str): The source stream to sync from. This can be a table, a query, or a path.
        target_object (str, optional): The target object to sync to. This can be a table, or a path. Defaults to the template of "{{target_schema}}.{{stream_schema}}_{{stream_table}}". See the Sling documentation for more information. https://docs.slingdata.io/sling-cli/replication
        mode (SlingMode, optional): The sync mode to use when syncing. Defaults to `full-refresh`.
        primary_key (Optional[Union[str, List[str]]], optional): The optional primary key to use when syncing.
        update_key (Optional[str], optional): The optional update key to use when syncing.
        source_options (Optional[Dict[str, Any]], optional): Any optional Sling source options to use when syncing.
        target_options (Optional[Dict[str, Any]], optional): Any optional target options to use when syncing.

    Examples:
        Creating a Sling asset that syncs from a database to a data warehouse:

        .. code-block:: python

            source = SlingConnectionResource(
                type="postgres",
                host=EnvVar("POSTGRES_HOST"),
                port=EnvVar("POSTGRES_PORT"),
                user=EnvVar("POSTGRES_USER"),
                password=EnvVar("POSTGRES_PASSWORD"),
                database=EnvVar("POSTGRES_DATABASE"),
            )

            target = SlingConnectionResource(
                type="snowflake",
                account=EnvVar("SNOWFLAKE_ACCOUNT"),
                user=EnvVar("SNOWFLAKE_USER"),
                password=EnvVar("SNOWFLAKE_PASSWORD"),
                database=EnvVar("SNOWFLAKE_DATABASE"),
                warehouse=EnvVar("SNOWFLAKE_WAREHOUSE"),
            )

            asset_def = build_assets_from_sling_stream(
                    source=source,
                    target=target,
                    stream="main.orders",
                    target_object="main.orders",
                    mode=SlingMode.INCREMENTAL,
                    primary_key="id"
            )
    """
>>>>>>> cb080be97a (refactored to pass multiple streams into a builder to parallelize replication)
    sling_replicator = SlingStreamReplicator(
        source_connection=source,
        target_connection=target,
    )

<<<<<<< HEAD
    asset_names = []
    specs = []
    for stream in streams:
        asset_name = stream["stream_name"]
        if stream["stream_name"].startswith("file://"):
            asset_name = asset_name.split("/")[-1].replace(".", "_")
        asset_names.append(asset_name)

    specs = [AssetSpec(asset_name) for asset_name in asset_names]

    @multi_asset(
        name=f"sling_sync__{str(uuid.uuid4())[:8]}",
        compute_kind="sling",
        specs=specs,
        # required_resource_keys={source.???, target.???}, TODO: How do you get the resource key at this point in time?
    )
    def _sling_assets(context: AssetExecutionContext) -> Generator[MaterializeResult, None, None]:
=======
 
    asset_names = []
    specs = []
    for stream in streams:
        # sanitize the stream name to a valid asset name, matching the regex A-Za-z0-9
        asset_name = stream["stream_name"].replace(".", "_")

        if asset_name.startswith("file://"):
            asset_name = asset_name.split("/")[-1]
        asset_names.append(asset_name)

    specs = [AssetSpec(asset_name) for asset_name in asset_names]

    @multi_asset(
        name=f"sling_sync__{str(uuid.uuid4())[:8]}",
        compute_kind="sling",
        specs=specs
    )
    def _sling_assets(context: AssetExecutionContext) -> MaterializeResult:
>>>>>>> cb080be97a (refactored to pass multiple streams into a builder to parallelize replication)
        last_row_count_observed = None

        for stdout_line in sling_replicator.sync(
            streams=streams,
            mode=mode,
            target_object=target_object,
            source_options=source_options,
            target_options=target_options,
        ):
            match = re.search(r"(\d+) rows", stdout_line)
            if match:
                last_row_count_observed = int(match.group(1))
            context.log.info(stdout_line)

        for spec in specs:
            yield MaterializeResult(
                asset_key=spec.key,
                metadata=(
                    {}
                    if last_row_count_observed is None
                    else {"row_count": last_row_count_observed}
                ),
            )

    return _sling_assets
