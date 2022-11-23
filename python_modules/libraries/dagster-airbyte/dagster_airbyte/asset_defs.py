import hashlib
import inspect
import os
import re
from abc import abstractmethod
from functools import partial
from itertools import chain
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    cast,
)

import yaml
from dagster_airbyte.resources import AirbyteResource
from dagster_airbyte.types import AirbyteTableMetadata
from dagster_airbyte.utils import (
    generate_materializations,
    generate_table_schema,
    is_basic_normalization_operation,
)

from dagster import AssetKey, AssetOut, Output, ResourceDefinition
from dagster import _check as check
from dagster._annotations import experimental
from dagster._core.definitions import AssetsDefinition, multi_asset
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.events import CoercibleToAssetKeyPrefix
from dagster._core.definitions.metadata import MetadataValue, TableSchemaMetadataValue
from dagster._core.definitions.metadata.table import TableSchema
from dagster._core.execution.context.init import build_init_resource_context
from dagster._utils import merge_dicts


def _build_airbyte_asset_defn_metadata(
    connection_id: str,
    destination_tables: Sequence[str],
    table_to_asset_key_fn: Callable[[str], AssetKey],
    asset_key_prefix: Optional[Sequence[str]] = None,
    normalization_tables: Optional[Mapping[str, Set[str]]] = None,
    upstream_assets: Optional[Iterable[AssetKey]] = None,
    group_name: Optional[str] = None,
    io_manager_key: Optional[str] = None,
    schema_by_table_name: Optional[Mapping[str, TableSchema]] = None,
) -> AssetsDefinitionCacheableData:

    asset_key_prefix = (
        check.opt_sequence_param(asset_key_prefix, "asset_key_prefix", of_type=str) or []
    )

    # Generate a list of outputs, the set of destination tables plus any affiliated
    # normalization tables
    tables = list(
        chain.from_iterable(
            chain(
                [destination_tables], normalization_tables.values() if normalization_tables else []
            )
        )
    )

    outputs = {
        table: AssetKey([*asset_key_prefix, *table_to_asset_key_fn(table).path]) for table in tables
    }

    internal_deps: Dict[str, Set[AssetKey]] = {}

    normalization_tables = (
        {k: list(v) for k, v in normalization_tables.items()} if normalization_tables else {}
    )

    # If normalization tables are specified, we need to add a dependency from the destination table
    # to the affilitated normalization table
    if normalization_tables:
        for base_table, derived_tables in normalization_tables.items():
            for derived_table in derived_tables:
                internal_deps[derived_table] = {
                    AssetKey([*asset_key_prefix, *table_to_asset_key_fn(base_table).path])
                }

    # All non-normalization tables depend on any user-provided upstream assets
    for table in destination_tables:
        internal_deps[table] = set(upstream_assets or [])

    return AssetsDefinitionCacheableData(
        keys_by_input_name={asset_key.path[-1]: asset_key for asset_key in upstream_assets}
        if upstream_assets
        else {},
        keys_by_output_name=outputs,
        internal_asset_deps=internal_deps,
        group_name=group_name,
        key_prefix=asset_key_prefix,
        can_subset=False,
        metadata_by_output_name={
            table: {"table_schema": MetadataValue.table_schema(schema_by_table_name[table])}
            for table in tables
        }
        if schema_by_table_name
        else None,
        extra_metadata={
            "connection_id": connection_id,
            "group_name": group_name,
            "destination_tables": destination_tables,
            "normalization_tables": normalization_tables,
            "io_manager_key": io_manager_key,
        },
    )


def _build_airbyte_assets_from_metadata(
    assets_defn_meta: AssetsDefinitionCacheableData,
    resource_defs: Optional[Mapping[str, ResourceDefinition]],
) -> AssetsDefinition:

    metadata = cast(Mapping[str, Any], assets_defn_meta.extra_metadata)
    connection_id = cast(str, metadata["connection_id"])
    group_name = cast(Optional[str], metadata["group_name"])
    destination_tables = cast(List[str], metadata["destination_tables"])
    normalization_tables = cast(Mapping[str, List[str]], metadata["normalization_tables"])
    io_manager_key = cast(Optional[str], metadata["io_manager_key"])

    @multi_asset(
        name=f"airbyte_sync_{connection_id[:5]}",
        non_argument_deps=set((assets_defn_meta.keys_by_input_name or {}).values()),
        outs={
            k: AssetOut(
                key=v,
                metadata={
                    k: cast(TableSchemaMetadataValue, v)
                    for k, v in assets_defn_meta.metadata_by_output_name.get(k, {}).items()
                }
                if assets_defn_meta.metadata_by_output_name
                else None,
                io_manager_key=io_manager_key,
            )
            for k, v in (assets_defn_meta.keys_by_output_name or {}).items()
        },
        internal_asset_deps={
            k: set(v) for k, v in (assets_defn_meta.internal_asset_deps or {}).items()
        },
        required_resource_keys={"airbyte"},
        compute_kind="airbyte",
        group_name=group_name,
        resource_defs=resource_defs,
    )
    def _assets(context):
        ab_output = context.resources.airbyte.sync_and_poll(connection_id=connection_id)
        for materialization in generate_materializations(
            ab_output, assets_defn_meta.key_prefix or []
        ):
            table_name = materialization.asset_key.path[-1]
            if table_name in destination_tables:
                yield Output(
                    value=None,
                    output_name=table_name,
                    metadata={
                        entry.label: entry.entry_data for entry in materialization.metadata_entries
                    },
                )
                # Also materialize any normalization tables affiliated with this destination
                # e.g. nested objects, lists etc
                if normalization_tables:
                    for dependent_table in normalization_tables.get(table_name, set()):
                        yield Output(
                            value=None,
                            output_name=dependent_table,
                        )
            else:
                yield materialization

    return _assets


@experimental
def build_airbyte_assets(
    connection_id: str,
    destination_tables: Sequence[str],
    asset_key_prefix: Optional[Sequence[str]] = None,
    normalization_tables: Optional[Mapping[str, Set[str]]] = None,
    upstream_assets: Optional[Set[AssetKey]] = None,
    schema_by_table_name: Optional[Mapping[str, TableSchema]] = None,
) -> Sequence[AssetsDefinition]:
    """
    Builds a set of assets representing the tables created by an Airbyte sync operation.

    Args:
        connection_id (str): The Airbyte Connection ID that this op will sync. You can retrieve this
            value from the "Connections" tab of a given connector in the Airbyte UI.
        destination_tables (List[str]): The names of the tables that you want to be represented
            in the Dagster asset graph for this sync. This will generally map to the name of the
            stream in Airbyte, unless a stream prefix has been specified in Airbyte.
        normalization_tables (Optional[Mapping[str, List[str]]]): If you are using Airbyte's
            normalization feature, you may specify a mapping of destination table to a list of
            derived tables that will be created by the normalization process.
        asset_key_prefix (Optional[List[str]]): A prefix for the asset keys inside this asset.
            If left blank, assets will have a key of `AssetKey([table_name])`.
        upstream_assets (Optional[Set[AssetKey]]): A list of assets to add as sources.
    """

    asset_key_prefix = check.opt_sequence_param(asset_key_prefix, "asset_key_prefix", of_type=str)

    # Generate a list of outputs, the set of destination tables plus any affiliated
    # normalization tables
    tables = chain.from_iterable(
        chain([destination_tables], normalization_tables.values() if normalization_tables else [])
    )
    outputs = {
        table: AssetOut(
            key=AssetKey([*asset_key_prefix, table]),
            metadata={"table_schema": MetadataValue.table_schema(schema_by_table_name[table])}
            if schema_by_table_name
            else None,
        )
        for table in tables
    }

    internal_deps = {}

    # If normalization tables are specified, we need to add a dependency from the destination table
    # to the affilitated normalization table
    if normalization_tables:
        for base_table, derived_tables in normalization_tables.items():
            for derived_table in derived_tables:
                internal_deps[derived_table] = {AssetKey([*asset_key_prefix, base_table])}

    # All non-normalization tables depend on any user-provided upstream assets
    for table in destination_tables:
        internal_deps[table] = upstream_assets or set()

    @multi_asset(
        name=f"airbyte_sync_{connection_id[:5]}",
        non_argument_deps=upstream_assets or set(),
        outs=outputs,
        internal_asset_deps=internal_deps,
        required_resource_keys={"airbyte"},
        compute_kind="airbyte",
    )
    def _assets(context):
        ab_output = context.resources.airbyte.sync_and_poll(connection_id=connection_id)
        for materialization in generate_materializations(ab_output, asset_key_prefix):
            table_name = materialization.asset_key.path[-1]
            if table_name in destination_tables:
                yield Output(
                    value=None,
                    output_name=table_name,
                    metadata={
                        entry.label: entry.entry_data for entry in materialization.metadata_entries
                    },
                )
                # Also materialize any normalization tables affiliated with this destination
                # e.g. nested objects, lists etc
                if normalization_tables:
                    for dependent_table in normalization_tables.get(table_name, set()):
                        yield Output(
                            value=None,
                            output_name=dependent_table,
                        )
            else:
                yield materialization

    return [_assets]


def _get_schema_types(schema: Mapping[str, Any]) -> Sequence[str]:
    """
    Given a schema definition, return a list of data types that are valid for this schema.
    """
    types = schema.get("types") or schema.get("type")
    if not types:
        return []
    if isinstance(types, str):
        return [types]
    return types


def _get_sub_schemas(schema: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    """
    Returns a list of sub-schema definitions for a given schema. This is used to handle union types.
    """
    return schema.get("anyOf") or schema.get("oneOf") or [schema]


def _get_normalization_tables_for_schema(
    key: str, schema: Mapping[str, Any], prefix: str = ""
) -> Mapping[str, AirbyteTableMetadata]:
    """
    Recursively traverses a schema, returning metadata for the tables that will be created by the Airbyte
    normalization process.

    For example, a table `cars` with a nested object field `limited_editions` will produce the tables
    `cars` and `cars_limited_editions`.

    For more information on Airbyte's normalization process, see:
    https://docs.airbyte.com/understanding-airbyte/basic-normalization/#nesting
    """

    out: Dict[str, AirbyteTableMetadata] = {}
    # Object types are broken into a new table, as long as they have children

    sub_schemas = _get_sub_schemas(schema)

    for sub_schema in sub_schemas:
        schema_types = _get_schema_types(sub_schema)
        if not schema_types:
            continue

        if "object" in schema_types and len(sub_schema.get("properties", {})) > 0:
            out[prefix + key] = AirbyteTableMetadata(
                schema=generate_table_schema(sub_schema.get("properties", {}))
            )
            for k, v in sub_schema["properties"].items():
                out = merge_dicts(
                    out, _get_normalization_tables_for_schema(k, v, f"{prefix}{key}_")
                )
        # Array types are also broken into a new table
        elif "array" in schema_types:
            out[prefix + key] = AirbyteTableMetadata(
                schema=generate_table_schema(sub_schema.get("items", {}).get("properties", {}))
            )
            if sub_schema.get("items", {}).get("properties"):
                for k, v in sub_schema["items"]["properties"].items():
                    out = merge_dicts(
                        out, _get_normalization_tables_for_schema(k, v, f"{prefix}{key}_")
                    )

    return out


def _clean_name(name: str) -> str:
    """
    Cleans an input to be a valid Dagster asset name.
    """
    return re.sub(r"[^a-z0-9]+", "_", name.lower())


class AirbyteConnectionMetadata(
    NamedTuple(
        "_AirbyteConnectionMetadata",
        [
            ("name", str),
            ("stream_prefix", str),
            ("has_basic_normalization", bool),
            ("stream_data", List[Mapping[str, Any]]),
        ],
    )
):
    """
    Contains information about an Airbyte connection.

    Attributes:
        name (str): The name of the connection.
        stream_prefix (str): A prefix to add to all stream names.
        has_basic_normalization (bool): Whether or not the connection has basic normalization enabled.
        stream_data (List[Mapping[str, Any]]): Unparsed list of dicts with information about each stream.
    """

    @classmethod
    def from_api_json(
        cls, contents: Mapping[str, Any], operations: Mapping[str, Any]
    ) -> "AirbyteConnectionMetadata":
        return cls(
            name=contents["name"],
            stream_prefix=contents.get("prefix", ""),
            has_basic_normalization=any(
                is_basic_normalization_operation(op.get("operatorConfiguration", {}))
                for op in operations.get("operations", [])
            ),
            stream_data=contents.get("syncCatalog", {}).get("streams", []),
        )

    @classmethod
    def from_config(cls, contents: Mapping[str, Any]) -> "AirbyteConnectionMetadata":
        config_contents = cast(Mapping[str, Any], contents.get("configuration"))
        check.invariant(
            config_contents is not None, "Airbyte connection config is missing 'configuration' key"
        )

        return cls(
            name=contents["resource_name"],
            stream_prefix=config_contents.get("prefix", ""),
            has_basic_normalization=any(
                is_basic_normalization_operation(op.get("operator_configuration", {}))
                for op in config_contents.get("operations", [])
            ),
            stream_data=config_contents.get("sync_catalog", {}).get("streams", []),
        )

    def parse_stream_tables(
        self, return_normalization_tables: bool = False
    ) -> Mapping[str, AirbyteTableMetadata]:
        """
        Parses the stream data and returns a mapping, with keys representing destination
        tables associated with each enabled stream and values representing any affiliated
        tables created by Airbyte's normalization process, if enabled.
        """

        tables: Dict[str, AirbyteTableMetadata] = {}

        enabled_streams = [
            stream for stream in self.stream_data if stream.get("config", {}).get("selected", False)
        ]

        for stream in enabled_streams:
            name = cast(str, stream.get("stream", {}).get("name"))
            prefixed_name = f"{self.stream_prefix}{name}"

            schema = (
                stream["stream"]["json_schema"]
                if "json_schema" in stream["stream"]
                else stream["stream"]["jsonSchema"]
            )
            normalization_tables: Dict[str, AirbyteTableMetadata] = {}
            if self.has_basic_normalization and return_normalization_tables:
                for k, v in schema["properties"].items():
                    for normalization_table_name, meta in _get_normalization_tables_for_schema(
                        k, v, f"{name}_"
                    ).items():
                        prefixed_norm_table_name = f"{self.stream_prefix}{normalization_table_name}"
                        normalization_tables[prefixed_norm_table_name] = meta
            tables[prefixed_name] = AirbyteTableMetadata(
                schema=generate_table_schema(schema["properties"]),
                normalization_tables=normalization_tables,
            )

        return tables


def _get_schema_by_table_name(
    stream_table_metadata: Mapping[str, AirbyteTableMetadata]
) -> Mapping[str, TableSchema]:

    schema_by_base_table_name = [(k, v.schema) for k, v in stream_table_metadata.items()]
    schema_by_normalization_table_name = list(
        chain.from_iterable(
            [
                [
                    (k, v.schema)
                    for k, v in cast(
                        Dict[str, AirbyteTableMetadata], meta.normalization_tables
                    ).items()
                ]
                for meta in stream_table_metadata.values()
            ]
        )
    )

    return dict(schema_by_normalization_table_name + schema_by_base_table_name)


class AirbyteCoreCacheableAssetsDefinition(CacheableAssetsDefinition):
    def __init__(
        self,
        key_prefix: Sequence[str],
        create_assets_for_normalization_tables: bool,
        connection_to_group_fn: Optional[Callable[[str], Optional[str]]],
        connection_to_io_manager_key_fn: Optional[Callable[[str], Optional[str]]],
        connection_filter: Optional[Callable[[AirbyteConnectionMetadata], bool]],
        connection_to_asset_key_fn: Optional[Callable[[AirbyteConnectionMetadata, str], AssetKey]],
    ):

        self._key_prefix = key_prefix
        self._create_assets_for_normalization_tables = create_assets_for_normalization_tables
        self._connection_to_group_fn = connection_to_group_fn
        self._connection_to_io_manager_key_fn = connection_to_io_manager_key_fn
        self._connection_filter = connection_filter
        self._connection_to_asset_key_fn: Callable[
            [AirbyteConnectionMetadata, str], AssetKey
        ] = connection_to_asset_key_fn or (lambda _, table: AssetKey(path=[table]))

        contents = hashlib.sha1()  # so that hexdigest is 40, not 64 bytes
        contents.update(",".join(key_prefix).encode("utf-8"))
        contents.update(str(create_assets_for_normalization_tables).encode("utf-8"))
        if connection_filter:
            contents.update(inspect.getsource(connection_filter).encode("utf-8"))

        super().__init__(unique_id=f"airbyte-{contents.hexdigest()}")

    @abstractmethod
    def _get_connections(self) -> Sequence[Tuple[str, AirbyteConnectionMetadata]]:
        pass

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:

        asset_defn_data: List[AssetsDefinitionCacheableData] = []
        for (connection_id, connection) in self._get_connections():

            stream_table_metadata = connection.parse_stream_tables(
                self._create_assets_for_normalization_tables
            )
            schema_by_table_name = _get_schema_by_table_name(stream_table_metadata)

            table_to_asset_key = partial(self._connection_to_asset_key_fn, connection)
            asset_data_for_conn = _build_airbyte_asset_defn_metadata(
                connection_id=connection_id,
                destination_tables=list(stream_table_metadata.keys()),
                normalization_tables={
                    table: set(metadata.normalization_tables.keys())
                    for table, metadata in stream_table_metadata.items()
                },
                asset_key_prefix=self._key_prefix,
                group_name=self._connection_to_group_fn(connection.name)
                if self._connection_to_group_fn
                else None,
                io_manager_key=self._connection_to_io_manager_key_fn(connection.name)
                if self._connection_to_io_manager_key_fn
                else None,
                schema_by_table_name=schema_by_table_name,
                table_to_asset_key_fn=table_to_asset_key,
            )

            asset_defn_data.append(asset_data_for_conn)

        return asset_defn_data

    def _build_definitions_with_resources(
        self,
        data: Sequence[AssetsDefinitionCacheableData],
        resource_defs: Optional[Mapping[str, ResourceDefinition]] = None,
    ) -> Sequence[AssetsDefinition]:
        return [_build_airbyte_assets_from_metadata(meta, resource_defs) for meta in data]

    def build_definitions(
        self, data: Sequence[AssetsDefinitionCacheableData]
    ) -> Sequence[AssetsDefinition]:
        return self._build_definitions_with_resources(data)


class AirbyteInstanceCacheableAssetsDefinition(AirbyteCoreCacheableAssetsDefinition):
    def __init__(
        self,
        airbyte_resource_def: ResourceDefinition,
        workspace_id: Optional[str],
        key_prefix: Sequence[str],
        create_assets_for_normalization_tables: bool,
        connection_to_group_fn: Optional[Callable[[str], Optional[str]]],
        connection_to_io_manager_key_fn: Optional[Callable[[str], Optional[str]]],
        connection_filter: Optional[Callable[[AirbyteConnectionMetadata], bool]],
        connection_to_asset_key_fn: Optional[Callable[[AirbyteConnectionMetadata, str], AssetKey]],
    ):
        super().__init__(
            key_prefix=key_prefix,
            create_assets_for_normalization_tables=create_assets_for_normalization_tables,
            connection_to_group_fn=connection_to_group_fn,
            connection_to_io_manager_key_fn=connection_to_io_manager_key_fn,
            connection_filter=connection_filter,
            connection_to_asset_key_fn=connection_to_asset_key_fn,
        )
        self._workspace_id = workspace_id
        self._airbyte_resource_def = airbyte_resource_def
        self._airbyte_instance: AirbyteResource = airbyte_resource_def(
            build_init_resource_context()
        )

    def _get_connections(self) -> Sequence[Tuple[str, AirbyteConnectionMetadata]]:
        workspace_id = self._workspace_id
        if not workspace_id:
            workspaces = cast(
                List[Dict[str, Any]],
                check.not_none(
                    self._airbyte_instance.make_request(endpoint="/workspaces/list", data={})
                ).get("workspaces", []),
            )

            check.invariant(len(workspaces) <= 1, "Airbyte instance has more than one workspace")
            check.invariant(len(workspaces) > 0, "Airbyte instance has no workspaces")

            workspace_id = workspaces[0].get("workspaceId")

        connections = cast(
            List[Dict[str, Any]],
            check.not_none(
                self._airbyte_instance.make_request(
                    endpoint="/connections/list", data={"workspaceId": workspace_id}
                )
            ).get("connections", []),
        )

        output_connections: List[Tuple[str, AirbyteConnectionMetadata]] = []
        for connection_json in connections:
            connection_id = cast(str, connection_json.get("connectionId"))

            operations_json = cast(
                Dict[str, Any],
                check.not_none(
                    self._airbyte_instance.make_request(
                        endpoint="/operations/list",
                        data={"connectionId": connection_id},
                    )
                ),
            )
            connection = AirbyteConnectionMetadata.from_api_json(connection_json, operations_json)

            # Filter out connections that don't match the filter function
            if self._connection_filter and not self._connection_filter(connection):
                continue

            output_connections.append((connection_id, connection))
        return output_connections

    def build_definitions(
        self, data: Sequence[AssetsDefinitionCacheableData]
    ) -> Sequence[AssetsDefinition]:
        return super()._build_definitions_with_resources(
            data, {"airbyte": self._airbyte_resource_def}
        )


class AirbyteYAMLCacheableAssetsDefinition(AirbyteCoreCacheableAssetsDefinition):
    def __init__(
        self,
        project_dir: str,
        workspace_id: Optional[str],
        key_prefix: Sequence[str],
        create_assets_for_normalization_tables: bool,
        connection_to_group_fn: Optional[Callable[[str], Optional[str]]],
        connection_to_io_manager_key_fn: Optional[Callable[[str], Optional[str]]],
        connection_filter: Optional[Callable[[AirbyteConnectionMetadata], bool]],
        connection_directories: Optional[Sequence[str]],
        connection_to_asset_key_fn: Optional[Callable[[AirbyteConnectionMetadata, str], AssetKey]],
    ):
        super().__init__(
            key_prefix=key_prefix,
            create_assets_for_normalization_tables=create_assets_for_normalization_tables,
            connection_to_group_fn=connection_to_group_fn,
            connection_to_io_manager_key_fn=connection_to_io_manager_key_fn,
            connection_filter=connection_filter,
            connection_to_asset_key_fn=connection_to_asset_key_fn,
        )
        self._workspace_id = workspace_id
        self._project_dir = project_dir
        self._connection_directories = connection_directories

    def _get_connections(self) -> Sequence[Tuple[str, AirbyteConnectionMetadata]]:
        connections_dir = os.path.join(self._project_dir, "connections")

        output_connections: List[Tuple[str, AirbyteConnectionMetadata]] = []

        connection_directories = self._connection_directories or os.listdir(connections_dir)
        for connection_name in connection_directories:

            connection_dir = os.path.join(connections_dir, connection_name)
            with open(os.path.join(connection_dir, "configuration.yaml"), encoding="utf-8") as f:
                connection = AirbyteConnectionMetadata.from_config(yaml.safe_load(f.read()))

            # Filter out connections that don't match the filter function
            if self._connection_filter and not self._connection_filter(connection):
                continue

            if self._workspace_id:
                state_file = f"state_{self._workspace_id}.yaml"
                check.invariant(
                    state_file in os.listdir(connection_dir),
                    f"Workspace state file {state_file} not found",
                )
            else:
                state_files = [
                    filename
                    for filename in os.listdir(connection_dir)
                    if filename.startswith("state_")
                ]
                check.invariant(
                    len(state_files) > 0,
                    "No state files found for connection {} in {}".format(
                        connection_name, connection_dir
                    ),
                )
                check.invariant(
                    len(state_files) <= 1,
                    "More than one state file found for connection {} in {}, specify a workspace_id to disambiguate".format(
                        connection_name, connection_dir
                    ),
                )
                state_file = state_files[0]

            with open(os.path.join(connection_dir, cast(str, state_file)), encoding="utf-8") as f:
                state = yaml.safe_load(f.read())
                connection_id = state.get("resource_id")

            output_connections.append((connection_id, connection))
        return output_connections


@experimental
def load_assets_from_airbyte_instance(
    airbyte: ResourceDefinition,
    workspace_id: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    create_assets_for_normalization_tables: bool = True,
    connection_to_group_fn: Optional[Callable[[str], Optional[str]]] = _clean_name,
    io_manager_key: Optional[str] = None,
    connection_to_io_manager_key_fn: Optional[Callable[[str], Optional[str]]] = None,
    connection_filter: Optional[Callable[[AirbyteConnectionMetadata], bool]] = None,
    connection_to_asset_key_fn: Optional[
        Callable[[AirbyteConnectionMetadata, str], AssetKey]
    ] = None,
) -> CacheableAssetsDefinition:
    """
    Loads Airbyte connection assets from a configured AirbyteResource instance. This fetches information
    about defined connections at initialization time, and will error on workspace load if the Airbyte
    instance is not reachable.

    Args:
        airbyte (ResourceDefinition): An AirbyteResource configured with the appropriate connection
            details.
        workspace_id (Optional[str]): The ID of the Airbyte workspace to load connections from. Only
            required if multiple workspaces exist in your instance.
        key_prefix (Optional[CoercibleToAssetKeyPrefix]): A prefix for the asset keys created.
        create_assets_for_normalization_tables (bool): If True, assets will be created for tables
            created by Airbyte's normalization feature. If False, only the destination tables
            will be created. Defaults to True.
        connection_to_group_fn (Optional[Callable[[str], Optional[str]]]): Function which returns an asset
            group name for a given Airbyte connection name. If None, no groups will be created. Defaults
            to a basic sanitization function.
        io_manager_key (Optional[str]): The IO manager key to use for all assets. Defaults to "io_manager".
            Use this if all assets should be loaded from the same source, otherwise use connection_to_io_manager_key_fn.
        connection_to_io_manager_key_fn (Optional[Callable[[str], Optional[str]]]): Function which returns an
            IO manager key for a given Airbyte connection name. When other ops are downstream of the loaded assets,
            the IOManager specified determines how the inputs to those ops are loaded. Defaults to "io_manager".
        connection_filter (Optional[Callable[[AirbyteConnectionMetadata], bool]]): Optional function which takes
            in connection metadata and returns False if the connection should be excluded from the output assets.
        connection_to_asset_key_fn (Optional[Callable[[AirbyteConnectionMetadata, str], AssetKey]]): Optional function which
            takes in connection metadata and table name and returns an asset key for the table. If None, the default asset
            key is based on the table name. Any asset key prefix will be applied to the output of this function.

    **Examples:**

    Loading all Airbyte connections as assets:

    .. code-block:: python

        from dagster_airbyte import airbyte_resource, load_assets_from_airbyte_instance

        airbyte_instance = airbyte_resource.configured(
            {
                "host": "localhost",
                "port": "8000",
            }
        )
        airbyte_assets = load_assets_from_airbyte_instance(airbyte_instance)

    Filtering the set of loaded connections:

    .. code-block:: python

        from dagster_airbyte import airbyte_resource, load_assets_from_airbyte_instance

        airbyte_instance = airbyte_resource.configured(
            {
                "host": "localhost",
                "port": "8000",
            }
        )
        airbyte_assets = load_assets_from_airbyte_instance(
            airbyte_instance,
            connection_filter=lambda meta: "snowflake" in meta.name,
        )
    """

    if isinstance(key_prefix, str):
        key_prefix = [key_prefix]
    key_prefix = check.list_param(key_prefix or [], "key_prefix", of_type=str)

    check.invariant(
        not io_manager_key or not connection_to_io_manager_key_fn,
        "Cannot specify both io_manager_key and connection_to_io_manager_key_fn",
    )
    if not connection_to_io_manager_key_fn:
        connection_to_io_manager_key_fn = lambda _: io_manager_key

    return AirbyteInstanceCacheableAssetsDefinition(
        airbyte_resource_def=airbyte,
        workspace_id=workspace_id,
        key_prefix=key_prefix,
        create_assets_for_normalization_tables=create_assets_for_normalization_tables,
        connection_to_group_fn=connection_to_group_fn,
        connection_to_io_manager_key_fn=connection_to_io_manager_key_fn,
        connection_filter=connection_filter,
        connection_to_asset_key_fn=connection_to_asset_key_fn,
    )


@experimental
def load_assets_from_airbyte_project(
    project_dir: str,
    workspace_id: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    create_assets_for_normalization_tables: bool = True,
    connection_to_group_fn: Optional[Callable[[str], Optional[str]]] = _clean_name,
    io_manager_key: Optional[str] = None,
    connection_to_io_manager_key_fn: Optional[Callable[[str], Optional[str]]] = None,
    connection_filter: Optional[Callable[[AirbyteConnectionMetadata], bool]] = None,
    connection_directories: Optional[Sequence[str]] = None,
    connection_to_asset_key_fn: Optional[
        Callable[[AirbyteConnectionMetadata, str], AssetKey]
    ] = None,
) -> CacheableAssetsDefinition:
    """
    Loads an Airbyte project into a set of Dagster assets.

    Point to the root folder of an Airbyte project synced using the Octavia CLI. For
    more information, see https://github.com/airbytehq/airbyte/tree/master/octavia-cli#octavia-import-all.

    Args:
        project_dir (str): The path to the root of your Airbyte project, containing sources, destinations,
            and connections folders.
        workspace_id (Optional[str]): The ID of the Airbyte workspace to load connections from. Only
            required if multiple workspace state YAMLfiles exist in the project.
        key_prefix (Optional[CoercibleToAssetKeyPrefix]): A prefix for the asset keys created.
        create_assets_for_normalization_tables (bool): If True, assets will be created for tables
            created by Airbyte's normalization feature. If False, only the destination tables
            will be created. Defaults to True.
        connection_to_group_fn (Optional[Callable[[str], Optional[str]]]): Function which returns an asset
            group name for a given Airbyte connection name. If None, no groups will be created. Defaults
            to a basic sanitization function.
        io_manager_key (Optional[str]): The IO manager key to use for all assets. Defaults to "io_manager".
            Use this if all assets should be loaded from the same source, otherwise use connection_to_io_manager_key_fn.
        connection_to_io_manager_key_fn (Optional[Callable[[str], Optional[str]]]): Function which returns an
            IO manager key for a given Airbyte connection name. When other ops are downstream of the loaded assets,
            the IOManager specified determines how the inputs to those ops are loaded. Defaults to "io_manager".
        connection_filter (Optional[Callable[[AirbyteConnectionMetadata], bool]]): Optional function which
            takes in connection metadata and returns False if the connection should be excluded from the output assets.
        connection_directories (Optional[List[str]]): Optional list of connection directories to load assets from.
            If omitted, all connections in the Airbyte project are loaded. May be faster than connection_filter
            if the project has many connections or if the connection yaml files are large.
        connection_to_asset_key_fn (Optional[Callable[[AirbyteConnectionMetadata, str], AssetKey]]): Optional function which
            takes in connection metadata and table name and returns an asset key for the table. If None, the default asset
            key is based on the table name. Any asset key prefix will be applied to the output of this function.

    **Examples:**

    Loading all Airbyte connections as assets:

    .. code-block:: python

        from dagster_airbyte import load_assets_from_airbyte_project

        airbyte_assets = load_assets_from_airbyte_project(
            project_dir="path/to/airbyte/project",
        )

    Filtering the set of loaded connections:

    .. code-block:: python

        from dagster_airbyte import load_assets_from_airbyte_project

        airbyte_assets = load_assets_from_airbyte_project(
            project_dir="path/to/airbyte/project",
            connection_filter=lambda meta: "snowflake" in meta.name,
        )
    """

    if isinstance(key_prefix, str):
        key_prefix = [key_prefix]
    key_prefix = check.list_param(key_prefix or [], "key_prefix", of_type=str)

    check.invariant(
        not io_manager_key or not connection_to_io_manager_key_fn,
        "Cannot specify both io_manager_key and connection_to_io_manager_key_fn",
    )
    if not connection_to_io_manager_key_fn:
        connection_to_io_manager_key_fn = lambda _: io_manager_key

    return AirbyteYAMLCacheableAssetsDefinition(
        project_dir=project_dir,
        workspace_id=workspace_id,
        key_prefix=key_prefix,
        create_assets_for_normalization_tables=create_assets_for_normalization_tables,
        connection_to_group_fn=connection_to_group_fn,
        connection_to_io_manager_key_fn=connection_to_io_manager_key_fn,
        connection_filter=connection_filter,
        connection_directories=connection_directories,
        connection_to_asset_key_fn=connection_to_asset_key_fn,
    )
