import hashlib
import inspect
import re
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Callable, NamedTuple, Optional, Union, cast

from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetsDefinition,
    OpExecutionContext,
    _check as check,
    multi_asset,
)
from dagster._annotations import beta, superseded
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.events import AssetMaterialization, CoercibleToAssetKeyPrefix, Output
from dagster._core.definitions.metadata import RawMetadataMapping
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster._core.definitions.metadata.table import TableColumn, TableSchema
from dagster._core.definitions.resource_definition import ResourceDefinition
from dagster._core.definitions.tags import build_kind_tag
from dagster._core.errors import DagsterStepOutputNotFoundError
from dagster._core.execution.context.init import build_init_resource_context
from dagster._core.utils import imap
from dagster._utils.log import get_dagster_logger

from dagster_fivetran.asset_decorator import fivetran_assets
from dagster_fivetran.resources import DEFAULT_POLL_INTERVAL, FivetranResource, FivetranWorkspace
from dagster_fivetran.translator import (
    ConnectorSelectorFn,
    DagsterFivetranTranslator,
    FivetranConnectorTableProps,
    FivetranMetadataSet,
    FivetranSchemaConfig,
)
from dagster_fivetran.utils import (
    generate_materializations,
    get_fivetran_connector_url,
    metadata_for_table,
)

DEFAULT_MAX_THREADPOOL_WORKERS = 10
logger = get_dagster_logger()


def _fetch_and_attach_col_metadata(
    fivetran_resource: FivetranResource, connector_id: str, materialization: AssetMaterialization
) -> AssetMaterialization:
    """Subroutine to fetch column metadata for a given table from the Fivetran API and attach it to the
    materialization.
    """
    try:
        schema_source_name = materialization.metadata["schema_source_name"].value
        table_source_name = materialization.metadata["table_source_name"].value

        table_conn_data = fivetran_resource.make_request(
            "GET",
            f"connectors/{connector_id}/schemas/{schema_source_name}/tables/{table_source_name}/columns",
        )
        columns = check.dict_elem(table_conn_data, "columns")
        table_columns = sorted(
            [
                TableColumn(name=col["name_in_destination"], type="")
                for col in columns.values()
                if "name_in_destination" in col and col.get("enabled")
            ],
            key=lambda col: col.name,
        )
        return materialization.with_metadata(
            {
                **materialization.metadata,
                **TableMetadataSet(column_schema=TableSchema(table_columns)),
            }
        )
    except Exception as e:
        logger.warning(
            "An error occurred while fetching column metadata for table %s",
            f"Exception: {e}",
            exc_info=True,
        )
        return materialization


def _build_fivetran_assets(
    connector_id: str,
    destination_tables: Sequence[str],
    fetch_column_metadata: bool,
    poll_timeout: Optional[float],
    poll_interval: float,
    io_manager_key: Optional[str],
    asset_key_prefix: Optional[Sequence[str]],
    metadata_by_table_name: Optional[Mapping[str, RawMetadataMapping]],
    table_to_asset_key_map: Optional[Mapping[str, AssetKey]],
    resource_defs: Optional[Mapping[str, ResourceDefinition]],
    group_name: Optional[str],
    infer_missing_tables: bool,
    op_tags: Optional[Mapping[str, Any]],
    asset_tags: Optional[Mapping[str, Any]],
    max_threadpool_workers: int = DEFAULT_MAX_THREADPOOL_WORKERS,
    translator: Optional[type[DagsterFivetranTranslator]] = None,
    connection_metadata: Optional["FivetranConnectionMetadata"] = None,
) -> Sequence[AssetsDefinition]:
    asset_key_prefix = check.opt_sequence_param(asset_key_prefix, "asset_key_prefix", of_type=str)
    check.invariant(
        (translator and connection_metadata) or not translator,
        "Translator and connection_metadata required.",
    )

    translator_instance = translator() if translator else None

    tracked_asset_keys = {
        table: AssetKey([*asset_key_prefix, *table.split(".")])
        if not translator_instance or not connection_metadata
        else translator_instance.get_asset_spec(
            FivetranConnectorTableProps(
                table=table,
                connector_id=connection_metadata.connector_id,
                name=connection_metadata.name,
                connector_url=connection_metadata.connector_url,
                schema_config=FivetranSchemaConfig.from_schema_config_details(
                    connection_metadata.schemas
                ),
                database=connection_metadata.database,
                service=connection_metadata.service,
            )
        ).key
        for table in destination_tables
    }
    user_facing_asset_keys = table_to_asset_key_map or tracked_asset_keys
    tracked_asset_key_to_user_facing_asset_key = {
        tracked_key: user_facing_asset_keys[table_name]
        for table_name, tracked_key in tracked_asset_keys.items()
    }

    _metadata_by_table_name = check.opt_mapping_param(
        metadata_by_table_name, "metadata_by_table_name", key_type=str
    )

    @multi_asset(
        name=f"fivetran_sync_{connector_id}",
        resource_defs=resource_defs,
        group_name=group_name,
        op_tags=op_tags,
        specs=[
            AssetSpec(
                key=user_facing_asset_keys[table],
                metadata={
                    **_metadata_by_table_name.get(table, {}),
                    **({"dagster/io_manager_key": io_manager_key} if io_manager_key else {}),
                },
                tags={
                    **build_kind_tag("fivetran"),
                    **(asset_tags or {}),
                },
            )
            if not translator_instance or not connection_metadata
            else translator_instance.get_asset_spec(
                FivetranConnectorTableProps(
                    table=table,
                    connector_id=connection_metadata.connector_id,
                    name=connection_metadata.name,
                    connector_url=connection_metadata.connector_url,
                    schema_config=FivetranSchemaConfig.from_schema_config_details(
                        connection_metadata.schemas
                    ),
                    database=connection_metadata.database,
                    service=connection_metadata.service,
                )
            )
            for table in tracked_asset_keys.keys()
        ],
    )
    def _assets(context: OpExecutionContext, fivetran: FivetranResource) -> Any:
        fivetran_output = fivetran.sync_and_poll(
            connector_id=connector_id,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )

        materialized_asset_keys = set()

        _map_fn: Callable[[AssetMaterialization], AssetMaterialization] = (
            lambda materialization: _fetch_and_attach_col_metadata(
                fivetran, connector_id, materialization
            )
            if fetch_column_metadata
            else materialization
        )
        with ThreadPoolExecutor(
            max_workers=max_threadpool_workers,
            thread_name_prefix=f"fivetran_{connector_id}",
        ) as executor:
            for materialization in imap(
                executor=executor,
                iterable=generate_materializations(
                    fivetran_output,
                    asset_key_prefix=asset_key_prefix,
                ),
                func=_map_fn,
            ):
                # scan through all tables actually created, if it was expected then emit an Output.
                # otherwise, emit a runtime AssetMaterialization
                if materialization.asset_key in tracked_asset_keys.values():
                    key = tracked_asset_key_to_user_facing_asset_key[materialization.asset_key]
                    yield Output(
                        value=None,
                        output_name=key.to_python_identifier(),
                        metadata=materialization.metadata,
                    )
                    materialized_asset_keys.add(materialization.asset_key)

                else:
                    yield materialization

        unmaterialized_asset_keys = set(tracked_asset_keys.values()) - materialized_asset_keys
        if infer_missing_tables:
            for asset_key in unmaterialized_asset_keys:
                key = tracked_asset_key_to_user_facing_asset_key[asset_key]

                yield Output(value=None, output_name=key.to_python_identifier())

        else:
            if unmaterialized_asset_keys:
                asset_key = next(iter(unmaterialized_asset_keys))
                output_name = "_".join(asset_key.path)
                raise DagsterStepOutputNotFoundError(
                    f"Core compute for {context.op_def.name} did not return an output for"
                    f' non-optional output "{output_name}".',
                    step_key=context.get_step_execution_context().step.key,
                    output_name=output_name,
                )

    return [_assets]


@superseded(additional_warn_text="Use the `fivetran_assets` decorator instead.")
def build_fivetran_assets(
    connector_id: str,
    destination_tables: Sequence[str],
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    poll_timeout: Optional[float] = None,
    io_manager_key: Optional[str] = None,
    asset_key_prefix: Optional[Sequence[str]] = None,
    metadata_by_table_name: Optional[Mapping[str, RawMetadataMapping]] = None,
    group_name: Optional[str] = None,
    infer_missing_tables: bool = False,
    op_tags: Optional[Mapping[str, Any]] = None,
    fetch_column_metadata: bool = True,
) -> Sequence[AssetsDefinition]:
    """Build a set of assets for a given Fivetran connector.

    Returns an AssetsDefinition which connects the specified ``asset_keys`` to the computation that
    will update them. Internally, executes a Fivetran sync for a given ``connector_id``, and
    polls until that sync completes, raising an error if it is unsuccessful. Requires the use of the
    :py:class:`~dagster_fivetran.fivetran_resource`, which allows it to communicate with the
    Fivetran API.

    Args:
        connector_id (str): The Fivetran Connector ID that this op will sync. You can retrieve this
            value from the "Setup" tab of a given connector in the Fivetran UI.
        destination_tables (List[str]): `schema_name.table_name` for each table that you want to be
            represented in the Dagster asset graph for this connection.
        poll_interval (float): The time (in seconds) that will be waited between successive polls.
        poll_timeout (Optional[float]): The maximum time that will waited before this operation is
            timed out. By default, this will never time out.
        io_manager_key (Optional[str]): The io_manager to be used to handle each of these assets.
        asset_key_prefix (Optional[List[str]]): A prefix for the asset keys inside this asset.
            If left blank, assets will have a key of `AssetKey([schema_name, table_name])`.
        metadata_by_table_name (Optional[Mapping[str, RawMetadataMapping]]): A mapping from destination
            table name to user-supplied metadata that should be associated with the asset for that table.
        group_name (Optional[str]): A string name used to organize multiple assets into groups. This
            group name will be applied to all assets produced by this multi_asset.
        infer_missing_tables (bool): If True, will create asset materializations for tables specified
            in destination_tables even if they are not present in the Fivetran sync output. This is useful
            in cases where Fivetran does not sync any data for a table and therefore does not include it
            in the sync output API response.
        op_tags (Optional[Dict[str, Any]]):
             A dictionary of tags for the op that computes the asset. Frameworks may expect and
             require certain metadata to be attached to a op. Values that are not strings will be
             json encoded and must meet the criteria that json.loads(json.dumps(value)) == value.
        fetch_column_metadata (bool): If True, will fetch column schema information for each table in the connector.
            This will induce additional API calls.

    **Examples:**

    Basic example:

        .. code-block:: python

            from dagster import AssetKey, repository, with_resources

            from dagster_fivetran import fivetran_resource
            from dagster_fivetran.assets import build_fivetran_assets

            my_fivetran_resource = fivetran_resource.configured(
                {
                    "api_key": {"env": "FIVETRAN_API_KEY"},
                    "api_secret": {"env": "FIVETRAN_API_SECRET"},
                }
            )

    Attaching metadata:

        .. code-block:: python

            fivetran_assets = build_fivetran_assets(
                connector_id="foobar",
                table_names=["schema1.table1", "schema2.table2"],
                metadata_by_table_name={
                    "schema1.table1": {
                        "description": "This is a table that contains foo and bar",
                    },
                    "schema2.table2": {
                        "description": "This is a table that contains baz and quux",
                    },
                },
            )
    """
    return _build_fivetran_assets(
        connector_id=connector_id,
        destination_tables=destination_tables,
        poll_interval=poll_interval,
        poll_timeout=poll_timeout,
        io_manager_key=io_manager_key,
        asset_key_prefix=asset_key_prefix,
        metadata_by_table_name=metadata_by_table_name,
        group_name=group_name,
        infer_missing_tables=infer_missing_tables,
        op_tags=op_tags,
        asset_tags=None,
        fetch_column_metadata=fetch_column_metadata,
        table_to_asset_key_map=None,
        resource_defs=None,
    )


class FivetranConnectionMetadata(
    NamedTuple(
        "_FivetranConnectionMetadata",
        [
            ("name", str),
            ("connector_id", str),
            ("connector_url", str),
            ("schemas", Mapping[str, Any]),
            ("database", Optional[str]),
            ("service", Optional[str]),
        ],
    )
):
    def build_asset_defn_metadata(
        self,
        key_prefix: Sequence[str],
        group_name: Optional[str],
        table_to_asset_key_fn: Callable[[str], AssetKey],
        io_manager_key: Optional[str] = None,
    ) -> AssetsDefinitionCacheableData:
        schema_table_meta: dict[str, RawMetadataMapping] = {}
        if "schemas" in self.schemas:
            schemas_inner = cast(dict[str, Any], self.schemas["schemas"])
            for schema in schemas_inner.values():
                if schema["enabled"]:
                    schema_name = schema["name_in_destination"]
                    schema_tables: dict[str, dict[str, Any]] = cast(
                        dict[str, dict[str, Any]], schema["tables"]
                    )
                    for table in schema_tables.values():
                        if table["enabled"]:
                            table_name = table["name_in_destination"]
                            schema_table_meta[f"{schema_name}.{table_name}"] = metadata_for_table(
                                table,
                                self.connector_url,
                                database=self.database,
                                schema=schema_name,
                                table=table_name,
                            )
        else:
            schema_table_meta[self.name] = {}

        outputs = {
            table: AssetKey([*key_prefix, *list(table_to_asset_key_fn(table).path)])
            for table in schema_table_meta.keys()
        }

        internal_deps: dict[str, set[AssetKey]] = {}

        return AssetsDefinitionCacheableData(
            keys_by_input_name={},
            keys_by_output_name=outputs,
            internal_asset_deps=internal_deps,
            group_name=group_name,
            key_prefix=key_prefix,
            can_subset=False,
            metadata_by_output_name=schema_table_meta,
            extra_metadata={
                "connector_id": self.connector_id,
                "io_manager_key": io_manager_key,
                "storage_kind": self.service,
                "connection_metadata": self.to_serializable_repr(),
            },
        )

    def to_serializable_repr(self) -> Any:
        return self._asdict()

    @staticmethod
    def from_serializable_repr(rep: Any) -> "FivetranConnectionMetadata":
        return FivetranConnectionMetadata(**rep)


def _build_fivetran_assets_from_metadata(
    assets_defn_meta: AssetsDefinitionCacheableData,
    resource_defs: Mapping[str, ResourceDefinition],
    poll_interval: float,
    poll_timeout: Optional[float],
    fetch_column_metadata: bool,
    translator: Optional[type[DagsterFivetranTranslator]] = None,
) -> AssetsDefinition:
    metadata = cast(Mapping[str, Any], assets_defn_meta.extra_metadata)
    connector_id = cast(str, metadata["connector_id"])
    io_manager_key = cast(Optional[str], metadata["io_manager_key"])
    storage_kind = cast(Optional[str], metadata.get("storage_kind"))

    connection_metadata = FivetranConnectionMetadata.from_serializable_repr(
        metadata["connection_metadata"]
    )

    return _build_fivetran_assets(
        connector_id=connector_id,
        destination_tables=list(
            assets_defn_meta.keys_by_output_name.keys()
            if assets_defn_meta.keys_by_output_name
            else []
        ),
        asset_key_prefix=list(assets_defn_meta.key_prefix or []),
        metadata_by_table_name=cast(
            dict[str, RawMetadataMapping], assets_defn_meta.metadata_by_output_name
        ),
        io_manager_key=io_manager_key,
        table_to_asset_key_map=assets_defn_meta.keys_by_output_name,
        resource_defs=resource_defs,
        group_name=assets_defn_meta.group_name,
        poll_interval=poll_interval,
        poll_timeout=poll_timeout,
        asset_tags=build_kind_tag(storage_kind) if storage_kind else None,
        fetch_column_metadata=fetch_column_metadata,
        infer_missing_tables=False,
        op_tags=None,
        translator=translator,
        connection_metadata=connection_metadata,
    )[0]


class FivetranInstanceCacheableAssetsDefinition(CacheableAssetsDefinition):
    def __init__(
        self,
        fivetran_resource_def: Union[FivetranResource, ResourceDefinition],
        key_prefix: Sequence[str],
        connector_to_group_fn: Optional[Callable[[str], Optional[str]]],
        connector_filter: Optional[Callable[[FivetranConnectionMetadata], bool]],
        connector_to_io_manager_key_fn: Optional[Callable[[str], Optional[str]]],
        connector_to_asset_key_fn: Optional[Callable[[FivetranConnectionMetadata, str], AssetKey]],
        destination_ids: Optional[list[str]],
        poll_interval: float,
        poll_timeout: Optional[float],
        fetch_column_metadata: bool,
        translator: Optional[type[DagsterFivetranTranslator]] = None,
    ):
        self._fivetran_resource_def = fivetran_resource_def
        if isinstance(fivetran_resource_def, FivetranResource):
            # We hold a copy which is not fully processed, this retains e.g. EnvVars for
            # display in the UI
            self._partially_initialized_fivetran_instance = fivetran_resource_def
            # The processed copy is used to query the Fivetran instance
            self._fivetran_instance: FivetranResource = (
                self._partially_initialized_fivetran_instance.process_config_and_initialize()
            )
        else:
            self._partially_initialized_fivetran_instance = fivetran_resource_def(
                build_init_resource_context()
            )
            self._fivetran_instance: FivetranResource = (
                self._partially_initialized_fivetran_instance
            )

        self._key_prefix = key_prefix
        self._connector_to_group_fn = connector_to_group_fn
        self._connection_filter = connector_filter
        self._connector_to_io_manager_key_fn = connector_to_io_manager_key_fn
        self._connector_to_asset_key_fn: Callable[[FivetranConnectionMetadata, str], AssetKey] = (
            connector_to_asset_key_fn or (lambda _, table: AssetKey(path=table.split(".")))
        )
        self._destination_ids = destination_ids
        self._poll_interval = poll_interval
        self._poll_timeout = poll_timeout
        self._fetch_column_metadata = fetch_column_metadata
        self._translator = translator

        contents = hashlib.sha1()
        contents.update(",".join(key_prefix).encode("utf-8"))
        if connector_filter:
            contents.update(inspect.getsource(connector_filter).encode("utf-8"))

        super().__init__(unique_id=f"fivetran-{contents.hexdigest()}")

    def _get_connectors(self) -> Sequence[FivetranConnectionMetadata]:
        output_connectors: list[FivetranConnectionMetadata] = []

        if not self._destination_ids:
            groups = self._fivetran_instance.make_request("GET", "groups")["items"]
        else:
            groups = [{"id": destination_id} for destination_id in self._destination_ids]

        for group in groups:
            group_id = group["id"]

            group_details = self._fivetran_instance.get_destination_details(group_id)
            database = group_details.get("config", {}).get("database")
            service = group_details.get("service")

            connectors = self._fivetran_instance.make_request(
                "GET", f"groups/{group_id}/connectors"
            )["items"]
            for connector in connectors:
                connector_id = connector["id"]

                connector_name = connector["schema"]

                setup_state = connector.get("status", {}).get("setup_state")
                if setup_state and setup_state in ("incomplete", "broken"):
                    continue

                connector_url = get_fivetran_connector_url(connector)

                schemas = self._fivetran_instance.make_request(
                    "GET", f"connectors/{connector_id}/schemas"
                )

                output_connectors.append(
                    FivetranConnectionMetadata(
                        name=connector_name,
                        connector_id=connector_id,
                        connector_url=connector_url,
                        schemas=schemas,
                        database=database,
                        service=service,
                    )
                )

        return output_connectors

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        asset_defn_data: list[AssetsDefinitionCacheableData] = []
        for connector in self._get_connectors():
            if not self._connection_filter or self._connection_filter(connector):
                table_to_asset_key = partial(self._connector_to_asset_key_fn, connector)
                asset_defn_data.append(
                    connector.build_asset_defn_metadata(
                        key_prefix=self._key_prefix,
                        group_name=(
                            self._connector_to_group_fn(connector.name)
                            if self._connector_to_group_fn
                            else None
                        ),
                        io_manager_key=(
                            self._connector_to_io_manager_key_fn(connector.name)
                            if self._connector_to_io_manager_key_fn
                            else None
                        ),
                        table_to_asset_key_fn=table_to_asset_key,
                    )
                )

        return asset_defn_data

    def build_definitions(
        self, data: Sequence[AssetsDefinitionCacheableData]
    ) -> Sequence[AssetsDefinition]:
        return [
            _build_fivetran_assets_from_metadata(
                meta,
                {
                    "fivetran": self._partially_initialized_fivetran_instance.get_resource_definition()
                },
                poll_interval=self._poll_interval,
                poll_timeout=self._poll_timeout,
                fetch_column_metadata=self._fetch_column_metadata,
                translator=self._translator,
            )
            for meta in data
        ]


def _clean_name(name: str) -> str:
    """Cleans an input to be a valid Dagster asset name."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower())


@superseded(
    additional_warn_text="Use the `build_fivetran_assets_definitions` factory instead.",
)
def load_assets_from_fivetran_instance(
    fivetran: Union[FivetranResource, ResourceDefinition],
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    connector_to_group_fn: Optional[Callable[[str], Optional[str]]] = None,
    io_manager_key: Optional[str] = None,
    connector_to_io_manager_key_fn: Optional[Callable[[str], Optional[str]]] = None,
    connector_filter: Optional[Callable[[FivetranConnectionMetadata], bool]] = None,
    connector_to_asset_key_fn: Optional[
        Callable[[FivetranConnectionMetadata, str], AssetKey]
    ] = None,
    destination_ids: Optional[list[str]] = None,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    poll_timeout: Optional[float] = None,
    fetch_column_metadata: bool = True,
    translator: Optional[type[DagsterFivetranTranslator]] = None,
) -> CacheableAssetsDefinition:
    """Loads Fivetran connector assets from a configured FivetranResource instance. This fetches information
    about defined connectors at initialization time, and will error on workspace load if the Fivetran
    instance is not reachable.

    Args:
        fivetran (ResourceDefinition): A FivetranResource configured with the appropriate connection
            details.
        key_prefix (Optional[CoercibleToAssetKeyPrefix]): A prefix for the asset keys created.
        connector_to_group_fn (Optional[Callable[[str], Optional[str]]]): Function which returns an asset
            group name for a given Fivetran connector name. If None, no groups will be created. Defaults
            to a basic sanitization function.
        io_manager_key (Optional[str]): The IO manager key to use for all assets. Defaults to "io_manager".
            Use this if all assets should be loaded from the same source, otherwise use connector_to_io_manager_key_fn.
        connector_to_io_manager_key_fn (Optional[Callable[[str], Optional[str]]]): Function which returns an
            IO manager key for a given Fivetran connector name. When other ops are downstream of the loaded assets,
            the IOManager specified determines how the inputs to those ops are loaded. Defaults to "io_manager".
        connector_filter (Optional[Callable[[FivetranConnectorMetadata], bool]]): Optional function which takes
            in connector metadata and returns False if the connector should be excluded from the output assets.
        connector_to_asset_key_fn (Optional[Callable[[FivetranConnectorMetadata, str], AssetKey]]): Optional function
            which takes in connector metadata and a table name and returns an AssetKey for that table. Defaults to
            a function that generates an AssetKey matching the table name, split by ".".
        destination_ids (Optional[List[str]]): A list of destination IDs to fetch connectors from. If None, all destinations
            will be polled for connectors.
        poll_interval (float): The time (in seconds) that will be waited between successive polls.
        poll_timeout (Optional[float]): The maximum time that will waited before this operation is
            timed out. By default, this will never time out.
        fetch_column_metadata (bool): If True, will fetch column schema information for each table in the connector.
            This will induce additional API calls.

    **Examples:**

    Loading all Fivetran connectors as assets:

    .. code-block:: python

        from dagster_fivetran import fivetran_resource, load_assets_from_fivetran_instance

        fivetran_instance = fivetran_resource.configured(
            {
                "api_key": "some_key",
                "api_secret": "some_secret",
            }
        )
        fivetran_assets = load_assets_from_fivetran_instance(fivetran_instance)

    Filtering the set of loaded connectors:

    .. code-block:: python

        from dagster_fivetran import fivetran_resource, load_assets_from_fivetran_instance

        fivetran_instance = fivetran_resource.configured(
            {
                "api_key": "some_key",
                "api_secret": "some_secret",
            }
        )
        fivetran_assets = load_assets_from_fivetran_instance(
            fivetran_instance,
            connector_filter=lambda meta: "snowflake" in meta.name,
        )
    """
    if isinstance(key_prefix, str):
        key_prefix = [key_prefix]
    key_prefix = check.list_param(key_prefix or [], "key_prefix", of_type=str)

    check.invariant(
        not (
            (
                key_prefix
                or connector_to_group_fn
                or io_manager_key
                or connector_to_io_manager_key_fn
                or connector_to_asset_key_fn
            )
            and translator
        ),
        "Cannot specify key_prefix, connector_to_group_fn, io_manager_key, connector_to_io_manager_key_fn, or connector_to_asset_key_fn when translator is specified",
    )
    connector_to_group_fn = connector_to_group_fn or _clean_name

    check.invariant(
        not io_manager_key or not connector_to_io_manager_key_fn,
        "Cannot specify both io_manager_key and connector_to_io_manager_key_fn",
    )
    if not connector_to_io_manager_key_fn:
        connector_to_io_manager_key_fn = lambda _: io_manager_key

    return FivetranInstanceCacheableAssetsDefinition(
        fivetran_resource_def=fivetran,
        key_prefix=key_prefix,
        connector_to_group_fn=connector_to_group_fn,
        connector_to_io_manager_key_fn=connector_to_io_manager_key_fn,
        connector_filter=connector_filter,
        connector_to_asset_key_fn=connector_to_asset_key_fn,
        destination_ids=destination_ids,
        poll_interval=poll_interval,
        poll_timeout=poll_timeout,
        fetch_column_metadata=fetch_column_metadata,
        translator=translator,
    )


# -----------------------
# Reworked assets factory
# -----------------------


@beta
def build_fivetran_assets_definitions(
    *,
    workspace: FivetranWorkspace,
    dagster_fivetran_translator: Optional[DagsterFivetranTranslator] = None,
    connector_selector_fn: Optional[ConnectorSelectorFn] = None,
) -> Sequence[AssetsDefinition]:
    """The list of AssetsDefinition for all connectors in the Fivetran workspace.

    Args:
        workspace (FivetranWorkspace): The Fivetran workspace to fetch assets from.
        dagster_fivetran_translator (Optional[DagsterFivetranTranslator], optional): The translator to use
            to convert Fivetran content into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterFivetranTranslator`.
        connector_selector_fn (Optional[ConnectorSelectorFn]):
                A function that allows for filtering which Fivetran connector assets are created for.

    Returns:
        List[AssetsDefinition]: The list of AssetsDefinition for all connectors in the Fivetran workspace.

    Examples:
        Sync the tables of a Fivetran connector:

        .. code-block:: python

            from dagster_fivetran import FivetranWorkspace, build_fivetran_assets_definitions

            import dagster as dg

            fivetran_workspace = FivetranWorkspace(
                account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
                api_key=dg.EnvVar("FIVETRAN_API_KEY"),
                api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
            )

            fivetran_assets = build_fivetran_assets_definitions(workspace=workspace)

            defs = dg.Definitions(
                assets=[*fivetran_assets],
                resources={"fivetran": fivetran_workspace},
            )

        Sync the tables of a Fivetran connector with a custom translator:

        .. code-block:: python

            from dagster_fivetran import (
                DagsterFivetranTranslator,
                FivetranConnectorTableProps,
                FivetranWorkspace,
                 build_fivetran_assets_definitions
            )

            import dagster as dg

            class CustomDagsterFivetranTranslator(DagsterFivetranTranslator):
                def get_asset_spec(self, props: FivetranConnectorTableProps) -> dg.AssetSpec:
                    default_spec = super().get_asset_spec(props)
                    return default_spec.replace_attributes(
                        key=default_spec.key.with_prefix("my_prefix"),
                    )


            fivetran_workspace = FivetranWorkspace(
                account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
                api_key=dg.EnvVar("FIVETRAN_API_KEY"),
                api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
            )

            fivetran_assets = build_fivetran_assets_definitions(
                workspace=workspace,
                dagster_fivetran_translator=CustomDagsterFivetranTranslator()
            )

            defs = dg.Definitions(
                assets=[*fivetran_assets],
                resources={"fivetran": fivetran_workspace},
            )

    """
    dagster_fivetran_translator = dagster_fivetran_translator or DagsterFivetranTranslator()
    connector_selector_fn = connector_selector_fn or (lambda connector: bool(connector))

    all_asset_specs = workspace.load_asset_specs(
        dagster_fivetran_translator=dagster_fivetran_translator,
        connector_selector_fn=connector_selector_fn,
    )

    connector_ids = {
        check.not_none(FivetranMetadataSet.extract(spec.metadata).connector_id)
        for spec in all_asset_specs
    }

    _asset_fns = []
    for connector_id in connector_ids:

        @fivetran_assets(
            connector_id=connector_id,
            workspace=workspace,
            name=connector_id,
            dagster_fivetran_translator=dagster_fivetran_translator,
            connector_selector_fn=connector_selector_fn,
        )
        def _asset_fn(context: AssetExecutionContext, fivetran: FivetranWorkspace):
            yield from fivetran.sync_and_poll(context=context)

        _asset_fns.append(_asset_fn)

    return _asset_fns
