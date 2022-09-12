import os
from itertools import chain
from typing import Any, Callable, Dict, List, Mapping, NamedTuple, Optional, Set, Union, cast

import yaml
from dagster_airbyte.utils import generate_materializations

from dagster import AssetKey, AssetOut, Output, SourceAsset
from dagster import _check as check
from dagster._annotations import experimental
from dagster._core.definitions import AssetsDefinition, multi_asset
from dagster._core.definitions.events import CoercibleToAssetKeyPrefix
from dagster._core.definitions.load_assets_from_modules import with_group


@experimental
def build_airbyte_assets(
    connection_id: str,
    destination_tables: List[str],
    asset_key_prefix: Optional[List[str]] = None,
    normalization_tables: Optional[Mapping[str, Set[str]]] = None,
    upstream_assets: Optional[Set[AssetKey]] = None,
) -> List[AssetsDefinition]:
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

    asset_key_prefix = check.opt_list_param(asset_key_prefix, "asset_key_prefix", of_type=str)

    # Generate a list of outputs, the set of destination tables plus any affiliated
    # normalization tables
    tables = chain.from_iterable(
        chain([destination_tables], normalization_tables.values() if normalization_tables else [])
    )
    outputs = {table: AssetOut(key=AssetKey(asset_key_prefix + [table])) for table in tables}

    internal_deps = {}

    # If normalization tables are specified, we need to add a dependency from the destination table
    # to the affilitated normalization table
    if normalization_tables:
        for base_table, derived_tables in normalization_tables.items():
            for derived_table in derived_tables:
                internal_deps[derived_table] = {AssetKey(asset_key_prefix + [base_table])}

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


def _get_normalization_tables_for_schema(
    key: str, schema: Mapping[str, Any], prefix: str = ""
) -> List[str]:
    """
    Recursively traverses a schema, returning a list of table names that will be created by the Airbyte
    normalization process.

    For example, a table `cars` with a nested object field `limited_editions` will produce the tables
    `cars` and `cars_limited_editions`.

    For more information on Airbyte's normalization process, see:
    https://docs.airbyte.com/understanding-airbyte/basic-normalization/#nesting
    """

    out = []
    # Object types are broken into a new table, as long as they have children
    if (
        schema["type"] == "object"
        or "object" in schema["type"]
        and len(schema.get("properties", {})) > 0
    ):
        out.append(prefix + key)
        for k, v in schema["properties"].items():
            out += _get_normalization_tables_for_schema(k, v, f"{prefix}{key}_")
    # Array types are also broken into a new table
    elif schema["type"] == "array" or "array" in schema["type"]:
        out.append(prefix + key)
        for k, v in schema["items"]["properties"].items():
            out += _get_normalization_tables_for_schema(k, v, f"{prefix}{key}_")
    return out


def _clean_name(name: str) -> str:
    """
    Cleans an input to be a valid Dagster asset name.
    """
    return "".join(c if c.isalnum() else "_" for c in name)


class AirbyteConnection(
    NamedTuple(
        "_AirbyteConnection",
        [
            ("name", str),
            ("source_config_path", str),
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
        source_config_path (str): The path to the Airbyte source configuration file.
        stream_prefix (str): A prefix to add to all stream names.
        has_basic_normalization (bool): Whether or not the connection has basic normalization enabled.
        stream_data (List[Mapping[str, Any]]): Unparsed list of dicts with information about each stream.
    """

    @classmethod
    def from_config(cls, contents: Mapping[str, Any]) -> "AirbyteConnection":
        config_contents = cast(Mapping[str, Any], contents.get("configuration"))
        check.invariant(
            config_contents is not None, "Airbyte connection config is missing 'configuration' key"
        )

        return cls(
            name=contents["resource_name"],
            source_config_path=contents["source_configuration_path"],
            stream_prefix=config_contents.get("prefix", ""),
            has_basic_normalization=any(
                op.get("operator_configuration", {}).get("operator_type") == "normalization"
                and op.get("operator_configuration", {}).get("normalization", {}).get("option")
                == "basic"
                for op in config_contents.get("operations", [])
            ),
            stream_data=config_contents.get("sync_catalog", {}).get("streams", []),
        )

    def parse_stream_tables(
        self, return_normalization_tables: bool = False
    ) -> Mapping[str, Set[str]]:
        """
        Parses the stream data and returns a mapping, with keys representing destination
        tables associated with each enabled stream and values representing any affiliated
        tables created by Airbyte's normalization process, if enabled.
        """

        tables: Dict[str, Set[str]] = {}

        enabled_streams = [
            stream for stream in self.stream_data if stream.get("config", {}).get("selected", False)
        ]

        for stream in enabled_streams:
            name = cast(str, stream.get("stream", {}).get("name"))
            prefixed_name = f"{self.stream_prefix}{name}"

            tables[prefixed_name] = set()
            if self.has_basic_normalization and return_normalization_tables:
                for k, v in stream["stream"]["json_schema"]["properties"].items():
                    for normalization_table_name in _get_normalization_tables_for_schema(
                        k, v, f"{name}_"
                    ):
                        prefixed_norm_table_name = f"{self.stream_prefix}{normalization_table_name}"
                        tables[prefixed_name].add(prefixed_norm_table_name)

        return tables


class AirbyteSource(NamedTuple("_AirbyteSource", [("name", str)])):
    """
    Contains information about an Airbyte source.

    Attributes:
        name (str): The name of the source.
    """

    @classmethod
    def from_config(cls, contents: Mapping[str, Any]) -> "AirbyteSource":
        return cls(name=contents["resource_name"])


@experimental
def load_assets_from_airbyte_project(
    project_dir: str,
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    source_key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    create_assets_for_normalization_tables: bool = True,
    connection_to_group_fn: Optional[Callable[[str], Optional[str]]] = _clean_name,
) -> List[Union[AssetsDefinition, SourceAsset]]:
    """
    Loads an Airbyte project into a set of Dagster assets.

    Point to the root folder of an Airbyte project synced using the Octavia CLI. For
    more information, see https://github.com/airbytehq/airbyte/tree/master/octavia-cli#octavia-import-all.

    Args:
        project_dir (str): The path to the root of your Airbyte project, containing sources, destinations,
            and connections folders.
        key_prefix (Optional[CoercibleToAssetKeyPrefix]): A prefix for the asset keys created.
        source_key_prefix (Optional[CoercibleToAssetKeyPrefix]): A prefix for the source asset keys produced.
        create_assets_for_normalization_tables (bool): If True, assets will be created for tables
            created by Airbyte's normalization feature. If False, only the destination tables
            will be created.
        connection_to_group_fn (Optional[Callable[[str], Optional[str]]]): Function which returns an asset
            group name for a given Airbyte connection name. If None, no groups will be created. Defaults
            to a basic sanitization function.
    """

    if isinstance(source_key_prefix, str):
        source_key_prefix = [source_key_prefix]
    source_key_prefix = check.list_param(source_key_prefix or [], "source_key_prefix", of_type=str)

    if isinstance(key_prefix, str):
        key_prefix = [key_prefix]
    key_prefix = check.list_param(key_prefix or [], "key_prefix", of_type=str)

    assets: List[AssetsDefinition] = []
    source_assets: Dict[str, SourceAsset] = {}

    connections_dir = os.path.join(project_dir, "connections")
    for connection_name in os.listdir(connections_dir):
        connection_dir = os.path.join(connections_dir, connection_name)
        with open(os.path.join(connection_dir, "configuration.yaml"), encoding="utf-8") as f:
            connection = AirbyteConnection.from_config(yaml.safe_load(f.read()))

        with open(os.path.join(project_dir, connection.source_config_path), encoding="utf-8") as f:
            source = AirbyteSource.from_config(yaml.safe_load(f.read()))
            if source.name not in source_assets:
                source_asset_key = AssetKey(source_key_prefix + [_clean_name(source.name)])
                source_assets[source.name] = SourceAsset(key=source_asset_key)

        state_file = next(
            (filename for filename in os.listdir(connection_dir) if filename.startswith("state_")),
            None,
        )
        check.invariant(
            state_file is not None,
            "No state file found for connection {} in {}".format(connection_name, connection_dir),
        )

        with open(os.path.join(connection_dir, cast(str, state_file)), encoding="utf-8") as f:
            state = yaml.safe_load(f.read())
            connection_id = state.get("resource_id")

        table_mapping = connection.parse_stream_tables(create_assets_for_normalization_tables)

        assets_for_connection = build_airbyte_assets(
            connection_id=connection_id,
            destination_tables=list(table_mapping.keys()),
            normalization_tables=table_mapping,
            asset_key_prefix=key_prefix,
            upstream_assets={source_asset_key},
        )

        if connection_to_group_fn:
            assets_for_connection = with_group(
                assets_for_connection, connection_to_group_fn(connection_name)
            )
        assets.extend(assets_for_connection)

    return assets + list(source_assets.values())
