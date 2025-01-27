import hashlib
import inspect
import os
from abc import abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from functools import partial
from itertools import chain
from typing import Any, Callable, NamedTuple, Optional, Union, cast

import yaml
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetOut,
    AutoMaterializePolicy,
    FreshnessPolicy,
    Nothing,
    Output,
    ResourceDefinition,
    SourceAsset,
    _check as check,
)
from dagster._annotations import experimental
from dagster._core.definitions import AssetsDefinition, multi_asset
from dagster._core.definitions.cacheable_assets import (
    AssetsDefinitionCacheableData,
    CacheableAssetsDefinition,
)
from dagster._core.definitions.events import CoercibleToAssetKey, CoercibleToAssetKeyPrefix
from dagster._core.definitions.metadata.metadata_set import TableMetadataSet
from dagster._core.definitions.metadata.table import TableSchema
from dagster._core.errors import DagsterInvalidDefinitionError, DagsterInvalidInvocationError
from dagster._core.execution.context.init import build_init_resource_context
from dagster._utils.merger import merge_dicts

from dagster_airbyte.asset_decorator import airbyte_assets
from dagster_airbyte.resources import (
    AirbyteCloudResource,
    AirbyteCloudWorkspace,
    AirbyteResource,
    BaseAirbyteResource,
)
from dagster_airbyte.translator import AirbyteMetadataSet, DagsterAirbyteTranslator
from dagster_airbyte.types import AirbyteTableMetadata
from dagster_airbyte.utils import (
    clean_name,
    generate_materializations,
    generate_table_schema,
    is_basic_normalization_operation,
)


def _table_to_output_name_fn(table: str) -> str:
    return table.replace("-", "_")


def _build_airbyte_asset_defn_metadata(
    connection_id: str,
    destination_tables: Sequence[str],
    destination_raw_table_names_by_table: Mapping[str, str],
    destination_database: Optional[str],
    destination_schema: Optional[str],
    table_to_asset_key_fn: Callable[[str], AssetKey],
    asset_key_prefix: Optional[Sequence[str]] = None,
    normalization_tables: Optional[Mapping[str, set[str]]] = None,
    normalization_raw_table_names_by_table: Optional[Mapping[str, str]] = None,
    upstream_assets: Optional[Iterable[AssetKey]] = None,
    group_name: Optional[str] = None,
    io_manager_key: Optional[str] = None,
    schema_by_table_name: Optional[Mapping[str, TableSchema]] = None,
    freshness_policy: Optional[FreshnessPolicy] = None,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
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
        _table_to_output_name_fn(table): AssetKey(
            [*asset_key_prefix, *table_to_asset_key_fn(table).path]
        )
        for table in tables
    }

    internal_deps: dict[str, set[AssetKey]] = {}

    metadata_encodable_normalization_tables = (
        {k: list(v) for k, v in normalization_tables.items()} if normalization_tables else {}
    )

    # If normalization tables are specified, we need to add a dependency from the destination table
    # to the affilitated normalization table
    if len(metadata_encodable_normalization_tables) > 0:
        for base_table, derived_tables in metadata_encodable_normalization_tables.items():
            for derived_table in derived_tables:
                internal_deps[derived_table] = {
                    AssetKey([*asset_key_prefix, *table_to_asset_key_fn(base_table).path])
                }

    # All non-normalization tables depend on any user-provided upstream assets
    for table in destination_tables:
        internal_deps[table] = set(upstream_assets or [])

    table_names: dict[str, str] = {}
    for table in destination_tables:
        if destination_database and destination_schema and table:
            # Use the destination raw table name to create the table name
            table_names[table] = ".".join(
                [
                    destination_database,
                    destination_schema,
                    destination_raw_table_names_by_table[table],
                ]
            )
            if normalization_tables and normalization_raw_table_names_by_table:
                for normalization_table in normalization_tables.get(table, set()):
                    table_names[normalization_table] = ".".join(
                        [
                            destination_database,
                            destination_schema,
                            destination_raw_table_names_by_table[table],
                            normalization_raw_table_names_by_table[normalization_table],
                        ]
                    )

    schema_by_table_name = schema_by_table_name if schema_by_table_name else {}

    return AssetsDefinitionCacheableData(
        keys_by_input_name=(
            {asset_key.path[-1]: asset_key for asset_key in upstream_assets}
            if upstream_assets
            else {}
        ),
        keys_by_output_name=outputs,
        internal_asset_deps=internal_deps,
        group_name=group_name,
        key_prefix=asset_key_prefix,
        can_subset=False,
        metadata_by_output_name=(
            {
                table: {
                    **TableMetadataSet(
                        column_schema=schema_by_table_name.get(table),
                        table_name=table_names.get(table),
                    ),
                }
                for table in tables
            }
        ),
        freshness_policies_by_output_name=(
            {output: freshness_policy for output in outputs} if freshness_policy else None
        ),
        auto_materialize_policies_by_output_name=(
            {output: auto_materialize_policy for output in outputs}
            if auto_materialize_policy
            else None
        ),
        extra_metadata={
            "connection_id": connection_id,
            "group_name": group_name,
            "destination_tables": destination_tables,
            "normalization_tables": metadata_encodable_normalization_tables,
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
    destination_tables = cast(list[str], metadata["destination_tables"])
    normalization_tables = cast(Mapping[str, list[str]], metadata["normalization_tables"])
    io_manager_key = cast(Optional[str], metadata["io_manager_key"])

    @multi_asset(
        name=f"airbyte_sync_{connection_id.replace('-', '_')}",
        deps=list((assets_defn_meta.keys_by_input_name or {}).values()),
        outs={
            k: AssetOut(
                key=v,
                metadata=(
                    assets_defn_meta.metadata_by_output_name.get(k)
                    if assets_defn_meta.metadata_by_output_name
                    else None
                ),
                io_manager_key=io_manager_key,
                freshness_policy=(
                    assets_defn_meta.freshness_policies_by_output_name.get(k)
                    if assets_defn_meta.freshness_policies_by_output_name
                    else None
                ),
                dagster_type=Nothing,
                auto_materialize_policy=assets_defn_meta.auto_materialize_policies_by_output_name.get(
                    k, None
                )
                if assets_defn_meta.auto_materialize_policies_by_output_name
                else None,
            )
            for k, v in (assets_defn_meta.keys_by_output_name or {}).items()
        },
        internal_asset_deps={
            k: set(v) for k, v in (assets_defn_meta.internal_asset_deps or {}).items()
        },
        compute_kind="airbyte",
        group_name=group_name,
        resource_defs=resource_defs,
    )
    def _assets(context, airbyte: AirbyteResource):
        ab_output = airbyte.sync_and_poll(connection_id=connection_id)
        for materialization in generate_materializations(
            ab_output, assets_defn_meta.key_prefix or []
        ):
            table_name = materialization.asset_key.path[-1]
            if table_name in destination_tables:
                yield Output(
                    value=None,
                    output_name=_table_to_output_name_fn(table_name),
                    metadata=materialization.metadata,
                )
                # Also materialize any normalization tables affiliated with this destination
                # e.g. nested objects, lists etc
                if normalization_tables:
                    for dependent_table in normalization_tables.get(table_name, set()):
                        yield Output(
                            value=None,
                            output_name=_table_to_output_name_fn(dependent_table),
                        )
            else:
                yield materialization

    return _assets


def build_airbyte_assets(
    connection_id: str,
    destination_tables: Sequence[str],
    destination_database: Optional[str] = None,
    destination_schema: Optional[str] = None,
    asset_key_prefix: Optional[Sequence[str]] = None,
    group_name: Optional[str] = None,
    normalization_tables: Optional[Mapping[str, set[str]]] = None,
    deps: Optional[Iterable[Union[CoercibleToAssetKey, AssetsDefinition, SourceAsset]]] = None,
    upstream_assets: Optional[set[AssetKey]] = None,
    schema_by_table_name: Optional[Mapping[str, TableSchema]] = None,
    freshness_policy: Optional[FreshnessPolicy] = None,
    stream_to_asset_map: Optional[Mapping[str, str]] = None,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
) -> Sequence[AssetsDefinition]:
    """Builds a set of assets representing the tables created by an Airbyte sync operation.

    Args:
        connection_id (str): The Airbyte Connection ID that this op will sync. You can retrieve this
            value from the "Connections" tab of a given connector in the Airbyte UI.
        destination_tables (List[str]): The names of the tables that you want to be represented
            in the Dagster asset graph for this sync. This will generally map to the name of the
            stream in Airbyte, unless a stream prefix has been specified in Airbyte.
        destination_database (Optional[str]): The name of the destination database.
        destination_schema (Optional[str]): The name of the destination schema.
        normalization_tables (Optional[Mapping[str, List[str]]]): If you are using Airbyte's
            normalization feature, you may specify a mapping of destination table to a list of
            derived tables that will be created by the normalization process.
        asset_key_prefix (Optional[List[str]]): A prefix for the asset keys inside this asset.
            If left blank, assets will have a key of `AssetKey([table_name])`.
        deps (Optional[Sequence[Union[AssetsDefinition, SourceAsset, str, AssetKey]]]):
            A list of assets to add as sources.
        upstream_assets (Optional[Set[AssetKey]]): Deprecated, use deps instead. A list of assets to add as sources.
        freshness_policy (Optional[FreshnessPolicy]): A freshness policy to apply to the assets
        stream_to_asset_map (Optional[Mapping[str, str]]): A mapping of an Airbyte stream name to a Dagster asset.
            This allows the use of the "prefix" setting in Airbyte with special characters that aren't valid asset names.
        auto_materialize_policy (Optional[AutoMaterializePolicy]): An auto materialization policy to apply to the assets.
    """
    if upstream_assets is not None and deps is not None:
        raise DagsterInvalidDefinitionError(
            "Cannot specify both deps and upstream_assets to build_airbyte_assets. Use only deps"
            " instead."
        )

    asset_key_prefix = check.opt_sequence_param(asset_key_prefix, "asset_key_prefix", of_type=str)

    # Generate a list of outputs, the set of destination tables plus any affiliated
    # normalization tables
    tables = chain.from_iterable(
        chain([destination_tables], normalization_tables.values() if normalization_tables else [])
    )

    table_names: dict[str, str] = {}
    for table in destination_tables:
        if destination_database and destination_schema and table:
            table_names[table] = ".".join([destination_database, destination_schema, table])
            if normalization_tables:
                for normalization_table in normalization_tables.get(table, set()):
                    table_names[normalization_table] = ".".join(
                        [
                            destination_database,
                            destination_schema,
                            table,
                            normalization_table,
                        ]
                    )

    schema_by_table_name = schema_by_table_name if schema_by_table_name else {}

    outputs = {
        table: AssetOut(
            key=AssetKey([*asset_key_prefix, table]),
            metadata=(
                {
                    **TableMetadataSet(
                        column_schema=schema_by_table_name.get(table),
                        table_name=table_names.get(table),
                    ),
                }
            ),
            freshness_policy=freshness_policy,
            auto_materialize_policy=auto_materialize_policy,
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

    upstream_deps = deps
    if upstream_assets is not None:
        upstream_deps = list(upstream_assets)

    # All non-normalization tables depend on any user-provided upstream assets
    for table in destination_tables:
        internal_deps[table] = set(upstream_deps) if upstream_deps else set()

    @multi_asset(
        name=f"airbyte_sync_{connection_id.replace('-', '_')}",
        deps=upstream_deps,
        outs=outputs,
        internal_asset_deps=internal_deps,
        compute_kind="airbyte",
        group_name=group_name,
    )
    def _assets(context, airbyte: BaseAirbyteResource):
        ab_output = airbyte.sync_and_poll(connection_id=connection_id)

        # No connection details (e.g. using Airbyte Cloud) means we just assume
        # that the outputs were produced
        if len(ab_output.connection_details) == 0:
            for table_name in destination_tables:
                yield Output(
                    value=None,
                    output_name=_table_to_output_name_fn(table_name),
                )
                if normalization_tables:
                    for dependent_table in normalization_tables.get(table_name, set()):
                        yield Output(
                            value=None,
                            output_name=_table_to_output_name_fn(dependent_table),
                        )
        else:
            for materialization in generate_materializations(
                ab_output, asset_key_prefix, stream_to_asset_map
            ):
                table_name = materialization.asset_key.path[-1]
                if table_name in destination_tables:
                    yield Output(
                        value=None,
                        output_name=_table_to_output_name_fn(table_name),
                        metadata=materialization.metadata,
                    )
                    # Also materialize any normalization tables affiliated with this destination
                    # e.g. nested objects, lists etc
                    if normalization_tables:
                        for dependent_table in normalization_tables.get(table_name, set()):
                            yield Output(
                                value=None,
                                output_name=_table_to_output_name_fn(dependent_table),
                            )
                else:
                    yield materialization

    return [_assets]


def _get_schema_types(schema: Mapping[str, Any]) -> Sequence[str]:
    """Given a schema definition, return a list of data types that are valid for this schema."""
    types = schema.get("types") or schema.get("type")
    if not types:
        return []
    if isinstance(types, str):
        return [types]
    return types


def _get_sub_schemas(schema: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    """Returns a list of sub-schema definitions for a given schema. This is used to handle union types."""
    return schema.get("anyOf") or schema.get("oneOf") or [schema]


def _get_normalization_tables_for_schema(
    key: str, schema: Mapping[str, Any], prefix: str = ""
) -> Mapping[str, AirbyteTableMetadata]:
    """Recursively traverses a schema, returning metadata for the tables that will be created by the Airbyte
    normalization process.

    For example, a table `cars` with a nested object field `limited_editions` will produce the tables
    `cars` and `cars_limited_editions`.

    For more information on Airbyte's normalization process, see:
    https://docs.airbyte.com/understanding-airbyte/basic-normalization/#nesting
    """
    out: dict[str, AirbyteTableMetadata] = {}
    # Object types are broken into a new table, as long as they have children

    sub_schemas = _get_sub_schemas(schema)

    for sub_schema in sub_schemas:
        schema_types = _get_schema_types(sub_schema)
        if not schema_types:
            continue

        if "object" in schema_types and len(sub_schema.get("properties", {})) > 0:
            out[prefix + key] = AirbyteTableMetadata(
                raw_table_name=key, schema=generate_table_schema(sub_schema.get("properties", {}))
            )
            for k, v in sub_schema["properties"].items():
                out = merge_dicts(
                    out, _get_normalization_tables_for_schema(k, v, f"{prefix}{key}_")
                )
        # Array types are also broken into a new table
        elif "array" in schema_types:
            out[prefix + key] = AirbyteTableMetadata(
                raw_table_name=key,
                schema=generate_table_schema(sub_schema.get("items", {}).get("properties", {})),
            )
            if sub_schema.get("items", {}).get("properties"):
                for k, v in sub_schema["items"]["properties"].items():
                    out = merge_dicts(
                        out, _get_normalization_tables_for_schema(k, v, f"{prefix}{key}_")
                    )

    return out


class AirbyteConnectionMetadata(
    NamedTuple(
        "_AirbyteConnectionMetadata",
        [
            ("name", str),
            ("stream_prefix", str),
            ("has_basic_normalization", bool),
            ("stream_data", list[Mapping[str, Any]]),
            ("destination", Mapping[str, Any]),
        ],
    )
):
    """Contains information about an Airbyte connection.

    Attributes:
        name (str): The name of the connection.
        stream_prefix (str): A prefix to add to all stream names.
        has_basic_normalization (bool): Whether or not the connection has basic normalization enabled.
        stream_data (List[Mapping[str, Any]]): Unparsed list of dicts with information about each stream.
    """

    @classmethod
    def from_api_json(
        cls,
        contents: Mapping[str, Any],
        operations: Mapping[str, Any],
        destination: Mapping[str, Any],
    ) -> "AirbyteConnectionMetadata":
        return cls(
            name=contents["name"],
            stream_prefix=contents.get("prefix", ""),
            has_basic_normalization=any(
                is_basic_normalization_operation(op.get("operatorConfiguration", {}))
                for op in operations.get("operations", [])
            ),
            stream_data=contents.get("syncCatalog", {}).get("streams", []),
            destination=destination,
        )

    @classmethod
    def from_config(
        cls, contents: Mapping[str, Any], destination: Mapping[str, Any]
    ) -> "AirbyteConnectionMetadata":
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
            destination=destination,
        )

    def parse_stream_tables(
        self, return_normalization_tables: bool = False
    ) -> Mapping[str, AirbyteTableMetadata]:
        """Parses the stream data and returns a mapping, with keys representing destination
        tables associated with each enabled stream and values representing any affiliated
        tables created by Airbyte's normalization process, if enabled.
        """
        tables: dict[str, AirbyteTableMetadata] = {}

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
            normalization_tables: dict[str, AirbyteTableMetadata] = {}
            schema_props = schema.get("properties", schema.get("items", {}).get("properties", {}))
            if self.has_basic_normalization and return_normalization_tables:
                for k, v in schema_props.items():
                    for normalization_table_name, meta in _get_normalization_tables_for_schema(
                        k, v, f"{name}_"
                    ).items():
                        prefixed_norm_table_name = f"{self.stream_prefix}{normalization_table_name}"
                        normalization_tables[prefixed_norm_table_name] = meta
            tables[prefixed_name] = AirbyteTableMetadata(
                raw_table_name=name,
                schema=generate_table_schema(schema_props),
                normalization_tables=normalization_tables,
            )

        return tables


def _get_schema_by_table_name(
    stream_table_metadata: Mapping[str, AirbyteTableMetadata],
) -> Mapping[str, TableSchema]:
    schema_by_base_table_name = [(k, v.schema) for k, v in stream_table_metadata.items()]
    schema_by_normalization_table_name = list(
        chain.from_iterable(
            [
                [
                    (k, v.schema)
                    for k, v in cast(
                        dict[str, AirbyteTableMetadata], meta.normalization_tables
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
        connection_meta_to_group_fn: Optional[Callable[[AirbyteConnectionMetadata], Optional[str]]],
        connection_to_io_manager_key_fn: Optional[Callable[[str], Optional[str]]],
        connection_filter: Optional[Callable[[AirbyteConnectionMetadata], bool]],
        connection_to_asset_key_fn: Optional[Callable[[AirbyteConnectionMetadata, str], AssetKey]],
        connection_to_freshness_policy_fn: Optional[
            Callable[[AirbyteConnectionMetadata], Optional[FreshnessPolicy]]
        ],
        connection_to_auto_materialize_policy_fn: Optional[
            Callable[[AirbyteConnectionMetadata], Optional[AutoMaterializePolicy]]
        ] = None,
    ):
        self._key_prefix = key_prefix
        self._create_assets_for_normalization_tables = create_assets_for_normalization_tables
        self._connection_meta_to_group_fn = connection_meta_to_group_fn
        self._connection_to_io_manager_key_fn = connection_to_io_manager_key_fn
        self._connection_filter = connection_filter
        self._connection_to_asset_key_fn: Callable[[AirbyteConnectionMetadata, str], AssetKey] = (
            connection_to_asset_key_fn or (lambda _, table: AssetKey(path=[table]))
        )
        self._connection_to_freshness_policy_fn = connection_to_freshness_policy_fn or (
            lambda _: None
        )
        self._connection_to_auto_materialize_policy_fn = (
            connection_to_auto_materialize_policy_fn or (lambda _: None)
        )

        contents = hashlib.sha1()  # so that hexdigest is 40, not 64 bytes
        contents.update(",".join(key_prefix).encode("utf-8"))
        contents.update(str(create_assets_for_normalization_tables).encode("utf-8"))
        if connection_filter:
            contents.update(inspect.getsource(connection_filter).encode("utf-8"))

        super().__init__(unique_id=f"airbyte-{contents.hexdigest()}")

    @abstractmethod
    def _get_connections(self) -> Sequence[tuple[str, AirbyteConnectionMetadata]]:
        pass

    def compute_cacheable_data(self) -> Sequence[AssetsDefinitionCacheableData]:
        asset_defn_data: list[AssetsDefinitionCacheableData] = []
        for connection_id, connection in self._get_connections():
            stream_table_metadata = connection.parse_stream_tables(
                self._create_assets_for_normalization_tables
            )
            schema_by_table_name = _get_schema_by_table_name(stream_table_metadata)

            destination_database = connection.destination.get("configuration", {}).get("database")
            destination_schema = connection.destination.get("configuration", {}).get("schema")

            table_to_asset_key = partial(self._connection_to_asset_key_fn, connection)

            destination_tables = list(stream_table_metadata.keys())
            destination_raw_table_names_by_table = {
                table: metadata.raw_table_name for table, metadata in stream_table_metadata.items()
            }
            normalization_tables = {
                table: set(metadata.normalization_tables.keys())
                for table, metadata in stream_table_metadata.items()
            }
            normalization_raw_table_names_by_table = {
                normalization_table: metadata.normalization_tables[
                    normalization_table
                ].raw_table_name
                for table, metadata in stream_table_metadata.items()
                for normalization_table in normalization_tables[table]
            }

            asset_data_for_conn = _build_airbyte_asset_defn_metadata(
                connection_id=connection_id,
                destination_tables=destination_tables,
                destination_raw_table_names_by_table=destination_raw_table_names_by_table,
                destination_database=destination_database,
                destination_schema=destination_schema,
                normalization_tables=normalization_tables,
                normalization_raw_table_names_by_table=normalization_raw_table_names_by_table,
                asset_key_prefix=self._key_prefix,
                group_name=(
                    self._connection_meta_to_group_fn(connection)
                    if self._connection_meta_to_group_fn
                    else None
                ),
                io_manager_key=(
                    self._connection_to_io_manager_key_fn(connection.name)
                    if self._connection_to_io_manager_key_fn
                    else None
                ),
                schema_by_table_name=schema_by_table_name,
                table_to_asset_key_fn=table_to_asset_key,
                freshness_policy=self._connection_to_freshness_policy_fn(connection),
                auto_materialize_policy=self._connection_to_auto_materialize_policy_fn(connection),
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
        airbyte_resource_def: Union[ResourceDefinition, AirbyteResource],
        workspace_id: Optional[str],
        key_prefix: Sequence[str],
        create_assets_for_normalization_tables: bool,
        connection_meta_to_group_fn: Optional[Callable[[AirbyteConnectionMetadata], Optional[str]]],
        connection_to_io_manager_key_fn: Optional[Callable[[str], Optional[str]]],
        connection_filter: Optional[Callable[[AirbyteConnectionMetadata], bool]],
        connection_to_asset_key_fn: Optional[Callable[[AirbyteConnectionMetadata, str], AssetKey]],
        connection_to_freshness_policy_fn: Optional[
            Callable[[AirbyteConnectionMetadata], Optional[FreshnessPolicy]]
        ],
        connection_to_auto_materialize_policy_fn: Optional[
            Callable[[AirbyteConnectionMetadata], Optional[AutoMaterializePolicy]]
        ] = None,
    ):
        super().__init__(
            key_prefix=key_prefix,
            create_assets_for_normalization_tables=create_assets_for_normalization_tables,
            connection_meta_to_group_fn=connection_meta_to_group_fn,
            connection_to_io_manager_key_fn=connection_to_io_manager_key_fn,
            connection_filter=connection_filter,
            connection_to_asset_key_fn=connection_to_asset_key_fn,
            connection_to_freshness_policy_fn=connection_to_freshness_policy_fn,
            connection_to_auto_materialize_policy_fn=connection_to_auto_materialize_policy_fn,
        )
        self._workspace_id = workspace_id

        if isinstance(airbyte_resource_def, AirbyteResource):
            # We hold a copy which is not fully processed, this retains e.g. EnvVars for
            # display in the UI
            self._partially_initialized_airbyte_instance = airbyte_resource_def
            # The processed copy is used to query the Airbyte instance
            self._airbyte_instance: AirbyteResource = (
                self._partially_initialized_airbyte_instance.process_config_and_initialize()
            )
        else:
            self._partially_initialized_airbyte_instance = airbyte_resource_def(
                build_init_resource_context()
            )
            self._airbyte_instance: AirbyteResource = self._partially_initialized_airbyte_instance

    def _get_connections(self) -> Sequence[tuple[str, AirbyteConnectionMetadata]]:
        workspace_id = self._workspace_id
        if not workspace_id:
            workspaces = cast(
                list[dict[str, Any]],
                check.not_none(
                    self._airbyte_instance.make_request(endpoint="/workspaces/list", data={})
                ).get("workspaces", []),
            )

            check.invariant(len(workspaces) <= 1, "Airbyte instance has more than one workspace")
            check.invariant(len(workspaces) > 0, "Airbyte instance has no workspaces")

            workspace_id = workspaces[0].get("workspaceId")

        connections = cast(
            list[dict[str, Any]],
            check.not_none(
                self._airbyte_instance.make_request(
                    endpoint="/connections/list", data={"workspaceId": workspace_id}
                )
            ).get("connections", []),
        )

        output_connections: list[tuple[str, AirbyteConnectionMetadata]] = []
        for connection_json in connections:
            connection_id = cast(str, connection_json.get("connectionId"))

            operations_json = cast(
                dict[str, Any],
                check.not_none(
                    self._airbyte_instance.make_request(
                        endpoint="/operations/list",
                        data={"connectionId": connection_id},
                    )
                ),
            )

            destination_id = cast(str, connection_json.get("destinationId"))
            destination_json = cast(
                dict[str, Any],
                check.not_none(
                    self._airbyte_instance.make_request(
                        endpoint="/destinations/get",
                        data={"destinationId": destination_id},
                    )
                ),
            )

            connection = AirbyteConnectionMetadata.from_api_json(
                connection_json, operations_json, destination_json
            )

            # Filter out connections that don't match the filter function
            if self._connection_filter and not self._connection_filter(connection):
                continue

            output_connections.append((connection_id, connection))
        return output_connections

    def build_definitions(
        self, data: Sequence[AssetsDefinitionCacheableData]
    ) -> Sequence[AssetsDefinition]:
        return super()._build_definitions_with_resources(
            data,
            {"airbyte": self._partially_initialized_airbyte_instance.get_resource_definition()},
        )


class AirbyteYAMLCacheableAssetsDefinition(AirbyteCoreCacheableAssetsDefinition):
    def __init__(
        self,
        project_dir: str,
        workspace_id: Optional[str],
        key_prefix: Sequence[str],
        create_assets_for_normalization_tables: bool,
        connection_meta_to_group_fn: Optional[Callable[[AirbyteConnectionMetadata], Optional[str]]],
        connection_to_io_manager_key_fn: Optional[Callable[[str], Optional[str]]],
        connection_filter: Optional[Callable[[AirbyteConnectionMetadata], bool]],
        connection_directories: Optional[Sequence[str]],
        connection_to_asset_key_fn: Optional[Callable[[AirbyteConnectionMetadata, str], AssetKey]],
        connection_to_freshness_policy_fn: Optional[
            Callable[[AirbyteConnectionMetadata], Optional[FreshnessPolicy]]
        ],
        connection_to_auto_materialize_policy_fn: Optional[
            Callable[[AirbyteConnectionMetadata], Optional[AutoMaterializePolicy]]
        ] = None,
    ):
        super().__init__(
            key_prefix=key_prefix,
            create_assets_for_normalization_tables=create_assets_for_normalization_tables,
            connection_meta_to_group_fn=connection_meta_to_group_fn,
            connection_to_io_manager_key_fn=connection_to_io_manager_key_fn,
            connection_filter=connection_filter,
            connection_to_asset_key_fn=connection_to_asset_key_fn,
            connection_to_freshness_policy_fn=connection_to_freshness_policy_fn,
            connection_to_auto_materialize_policy_fn=connection_to_auto_materialize_policy_fn,
        )
        self._workspace_id = workspace_id
        self._project_dir = project_dir
        self._connection_directories = connection_directories

    def _get_connections(self) -> Sequence[tuple[str, AirbyteConnectionMetadata]]:
        connections_dir = os.path.join(self._project_dir, "connections")

        output_connections: list[tuple[str, AirbyteConnectionMetadata]] = []

        connection_directories = self._connection_directories or os.listdir(connections_dir)
        for connection_name in connection_directories:
            connection_dir = os.path.join(connections_dir, connection_name)
            with open(os.path.join(connection_dir, "configuration.yaml"), encoding="utf-8") as f:
                connection_data = yaml.safe_load(f.read())

            destination_configuration_path = cast(
                str, connection_data.get("destination_configuration_path")
            )
            with open(
                os.path.join(self._project_dir, destination_configuration_path), encoding="utf-8"
            ) as f:
                destination_data = yaml.safe_load(f.read())

            connection = AirbyteConnectionMetadata.from_config(connection_data, destination_data)

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
                    f"No state files found for connection {connection_name} in {connection_dir}",
                )
                check.invariant(
                    len(state_files) <= 1,
                    f"More than one state file found for connection {connection_name} in {connection_dir}, specify a workspace_id"
                    " to disambiguate",
                )
                state_file = state_files[0]

            with open(os.path.join(connection_dir, cast(str, state_file)), encoding="utf-8") as f:
                state = yaml.safe_load(f.read())
                connection_id = state.get("resource_id")

            output_connections.append((connection_id, connection))
        return output_connections


def load_assets_from_airbyte_instance(
    airbyte: Union[AirbyteResource, ResourceDefinition],
    workspace_id: Optional[str] = None,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    create_assets_for_normalization_tables: bool = True,
    connection_to_group_fn: Optional[Callable[[str], Optional[str]]] = clean_name,
    connection_meta_to_group_fn: Optional[
        Callable[[AirbyteConnectionMetadata], Optional[str]]
    ] = None,
    io_manager_key: Optional[str] = None,
    connection_to_io_manager_key_fn: Optional[Callable[[str], Optional[str]]] = None,
    connection_filter: Optional[Callable[[AirbyteConnectionMetadata], bool]] = None,
    connection_to_asset_key_fn: Optional[
        Callable[[AirbyteConnectionMetadata, str], AssetKey]
    ] = None,
    connection_to_freshness_policy_fn: Optional[
        Callable[[AirbyteConnectionMetadata], Optional[FreshnessPolicy]]
    ] = None,
    connection_to_auto_materialize_policy_fn: Optional[
        Callable[[AirbyteConnectionMetadata], Optional[AutoMaterializePolicy]]
    ] = None,
) -> CacheableAssetsDefinition:
    """Loads Airbyte connection assets from a configured AirbyteResource instance. This fetches information
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
        connection_meta_to_group_fn (Optional[Callable[[AirbyteConnectionMetadata], Optional[str]]]): Function which
            returns an asset group name for a given Airbyte connection metadata. If None and connection_to_group_fn
            is None, no groups will be created
        io_manager_key (Optional[str]): The I/O manager key to use for all assets. Defaults to "io_manager".
            Use this if all assets should be loaded from the same source, otherwise use connection_to_io_manager_key_fn.
        connection_to_io_manager_key_fn (Optional[Callable[[str], Optional[str]]]): Function which returns an
            I/O manager key for a given Airbyte connection name. When other ops are downstream of the loaded assets,
            the IOManager specified determines how the inputs to those ops are loaded. Defaults to "io_manager".
        connection_filter (Optional[Callable[[AirbyteConnectionMetadata], bool]]): Optional function which takes
            in connection metadata and returns False if the connection should be excluded from the output assets.
        connection_to_asset_key_fn (Optional[Callable[[AirbyteConnectionMetadata, str], AssetKey]]): Optional function which
            takes in connection metadata and table name and returns an asset key for the table. If None, the default asset
            key is based on the table name. Any asset key prefix will be applied to the output of this function.
        connection_to_freshness_policy_fn (Optional[Callable[[AirbyteConnectionMetadata], Optional[FreshnessPolicy]]]): Optional function
            which takes in connection metadata and returns a freshness policy for the connection's assets. If None, no freshness policies
            will be applied to the assets.
        connection_to_auto_materialize_policy_fn (Optional[Callable[[AirbyteConnectionMetadata], Optional[AutoMaterializePolicy]]]): Optional
            function which takes in connection metadata and returns an auto materialization policy for the connection's assets. If None, no
            auto materialization policies will be applied to the assets.

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
    if isinstance(airbyte, AirbyteCloudResource):
        raise DagsterInvalidInvocationError(
            "load_assets_from_airbyte_instance is not yet supported for AirbyteCloudResource"
        )

    if isinstance(key_prefix, str):
        key_prefix = [key_prefix]
    key_prefix = check.list_param(key_prefix or [], "key_prefix", of_type=str)

    check.invariant(
        not io_manager_key or not connection_to_io_manager_key_fn,
        "Cannot specify both io_manager_key and connection_to_io_manager_key_fn",
    )
    if not connection_to_io_manager_key_fn:
        connection_to_io_manager_key_fn = lambda _: io_manager_key

    check.invariant(
        not connection_meta_to_group_fn
        or not connection_to_group_fn
        or connection_to_group_fn == clean_name,
        "Cannot specify both connection_meta_to_group_fn and connection_to_group_fn",
    )

    if not connection_meta_to_group_fn and connection_to_group_fn:
        connection_meta_to_group_fn = lambda meta: connection_to_group_fn(meta.name)

    return AirbyteInstanceCacheableAssetsDefinition(
        airbyte_resource_def=airbyte,
        workspace_id=workspace_id,
        key_prefix=key_prefix,
        create_assets_for_normalization_tables=create_assets_for_normalization_tables,
        connection_meta_to_group_fn=connection_meta_to_group_fn,
        connection_to_io_manager_key_fn=connection_to_io_manager_key_fn,
        connection_filter=connection_filter,
        connection_to_asset_key_fn=connection_to_asset_key_fn,
        connection_to_freshness_policy_fn=connection_to_freshness_policy_fn,
        connection_to_auto_materialize_policy_fn=connection_to_auto_materialize_policy_fn,
    )


# -----------------------
# Reworked assets factory
# -----------------------


@experimental
def build_airbyte_assets_definitions(
    *,
    workspace: AirbyteCloudWorkspace,
    dagster_airbyte_translator: Optional[DagsterAirbyteTranslator] = None,
) -> Sequence[AssetsDefinition]:
    """The list of AssetsDefinition for all connections in the Airbyte workspace.

    Args:
        workspace (AirbyteCloudWorkspace): The Airbyte workspace to fetch assets from.
        dagster_airbyte_translator (Optional[DagsterAirbyteTranslator], optional): The translator to use
            to convert Airbyte content into :py:class:`dagster.AssetSpec`.
            Defaults to :py:class:`DagsterAirbyteTranslator`.

    Returns:
        List[AssetsDefinition]: The list of AssetsDefinition for all connections in the Airbyte workspace.

    Examples:
        Sync the tables of a Airbyte connection:

        .. code-block:: python

            from dagster_airbyte import AirbyteCloudWorkspace, build_airbyte_assets_definitions

            import dagster as dg

            airbyte_workspace = AirbyteCloudWorkspace(
                workspace_id=dg.EnvVar("AIRBYTE_CLOUD_WORKSPACE_ID"),
                client_id=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_ID"),
                client_secret=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_SECRET"),
            )


            airbyte_assets = build_airbyte_assets_definitions(workspace=workspace)

            defs = dg.Definitions(
                assets=airbyte_assets,
                resources={"airbyte": airbyte_workspace},
            )

        Sync the tables of a Airbyte connection with a custom translator:

        .. code-block:: python

            from dagster_airbyte import (
                DagsterAirbyteTranslator,
                AirbyteConnectionTableProps,
                AirbyteCloudWorkspace,
                build_airbyte_assets_definitions
            )

            import dagster as dg

            class CustomDagsterAirbyteTranslator(DagsterAirbyteTranslator):
                def get_asset_spec(self, props: AirbyteConnectionTableProps) -> dg.AssetSpec:
                    default_spec = super().get_asset_spec(props)
                    return default_spec.merge_attributes(
                        metadata={"custom": "metadata"},
                    )

            airbyte_workspace = AirbyteCloudWorkspace(
                workspace_id=dg.EnvVar("AIRBYTE_CLOUD_WORKSPACE_ID"),
                client_id=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_ID"),
                client_secret=dg.EnvVar("AIRBYTE_CLOUD_CLIENT_SECRET"),
            )


            airbyte_assets = build_airbyte_assets_definitions(
                workspace=workspace,
                dagster_airbyte_translator=CustomDagsterAirbyteTranslator()
            )

            defs = dg.Definitions(
                assets=airbyte_assets,
                resources={"airbyte": airbyte_workspace},
            )
    """
    dagster_airbyte_translator = dagster_airbyte_translator or DagsterAirbyteTranslator()

    all_asset_specs = workspace.load_asset_specs(
        dagster_airbyte_translator=dagster_airbyte_translator
    )

    connections = {
        (
            check.not_none(AirbyteMetadataSet.extract(spec.metadata).connection_id),
            check.not_none(AirbyteMetadataSet.extract(spec.metadata).connection_name),
        )
        for spec in all_asset_specs
    }

    _asset_fns = []
    for connection_id, connection_name in connections:

        @airbyte_assets(
            connection_id=connection_id,
            workspace=workspace,
            name=clean_name(connection_name),
            group_name=clean_name(connection_name),
            dagster_airbyte_translator=dagster_airbyte_translator,
        )
        def _asset_fn(context: AssetExecutionContext, airbyte: AirbyteCloudWorkspace):
            yield from airbyte.sync_and_poll(context=context)

        _asset_fns.append(_asset_fn)

    return _asset_fns
