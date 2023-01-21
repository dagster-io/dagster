from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, cast

import dagster._check as check
from dagster import AssetKey, ResourceDefinition
from dagster._annotations import experimental, public
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.events import CoercibleToAssetKeyPrefix
from dagster._core.definitions.freshness_policy import FreshnessPolicy
from dagster._core.execution.context.init import build_init_resource_context
from dagster._utils.merger import deep_merge_dicts
from dagster_managed_elements import (
    ManagedElementCheckResult,
    ManagedElementDiff,
    ManagedElementError,
)
from dagster_managed_elements.types import (
    SECRET_MASK_VALUE,
    ManagedElementReconciler,
    is_key_secret,
)
from dagster_managed_elements.utils import UNSET, diff_dicts

from dagster_airbyte.asset_defs import (
    AirbyteConnectionMetadata,
    AirbyteInstanceCacheableAssetsDefinition,
    _clean_name,
)
from dagster_airbyte.managed.types import (
    AirbyteConnection,
    AirbyteDestination,
    AirbyteDestinationNamespace,
    AirbyteSource,
    AirbyteSyncMode,
    InitializedAirbyteConnection,
    InitializedAirbyteDestination,
    InitializedAirbyteSource,
)
from dagster_airbyte.resources import AirbyteResource
from dagster_airbyte.utils import is_basic_normalization_operation


def gen_configured_stream_json(
    source_stream: Mapping[str, Any], user_stream_config: Mapping[str, AirbyteSyncMode]
) -> Mapping[str, Any]:
    """
    Generates an Airbyte API stream defintiion based on the succinct user-provided config and the
    full stream definition from the source.
    """
    config = user_stream_config[source_stream["stream"]["name"]]
    return deep_merge_dicts(
        source_stream,
        {"config": config.to_json()},
    )


def _ignore_secrets_compare_fn(k: str, _cv: Any, dv: Any) -> Optional[bool]:
    if is_key_secret(k):
        return dv == SECRET_MASK_VALUE
    return None


def _diff_configs(
    config_dict: Mapping[str, Any], dst_dict: Mapping[str, Any], ignore_secrets: bool = True
) -> ManagedElementDiff:
    return diff_dicts(
        config_dict=config_dict,
        dst_dict=dst_dict,
        custom_compare_fn=_ignore_secrets_compare_fn if ignore_secrets else None,
    )


def diff_sources(
    config_src: Optional[AirbyteSource],
    curr_src: Optional[AirbyteSource],
    ignore_secrets: bool = True,
) -> ManagedElementCheckResult:
    """
    Utility to diff two AirbyteSource objects.
    """
    diff = _diff_configs(
        config_src.source_configuration if config_src else {},
        curr_src.source_configuration if curr_src else {},
        ignore_secrets,
    )
    if not diff.is_empty():
        name = config_src.name if config_src else curr_src.name if curr_src else "Unknown"
        return ManagedElementDiff().with_nested(name, diff)

    return ManagedElementDiff()


def diff_destinations(
    config_dst: Optional[AirbyteDestination],
    curr_dst: Optional[AirbyteDestination],
    ignore_secrets: bool = True,
) -> ManagedElementCheckResult:
    """
    Utility to diff two AirbyteDestination objects.
    """
    diff = _diff_configs(
        config_dst.destination_configuration if config_dst else {},
        curr_dst.destination_configuration if curr_dst else {},
        ignore_secrets,
    )
    if not diff.is_empty():
        name = config_dst.name if config_dst else curr_dst.name if curr_dst else "Unknown"
        return ManagedElementDiff().with_nested(name, diff)

    return ManagedElementDiff()


def conn_dict(conn: Optional[AirbyteConnection]) -> Mapping[str, Any]:
    if not conn:
        return {}
    return {
        "source": conn.source.name if conn.source else "Unknown",
        "destination": conn.destination.name if conn.destination else "Unknown",
        "normalize data": conn.normalize_data,
        "streams": {k: v.to_json() for k, v in conn.stream_config.items()},
        "destination namespace": conn.destination_namespace.name
        if isinstance(conn.destination_namespace, AirbyteDestinationNamespace)
        else conn.destination_namespace,
        "prefix": conn.prefix,
    }


OPTIONAL_STREAM_SETTINGS = ("cursorField", "primaryKey")


def _compare_stream_values(k: str, cv: str, _dv: str):
    """
    Don't register a diff for optional stream settings if the value is not set
    in the user-provided config, this means it will default to the value in the
    source.
    """
    return True if k in OPTIONAL_STREAM_SETTINGS and cv == UNSET else None


def diff_connections(
    config_conn: Optional[AirbyteConnection], curr_conn: Optional[AirbyteConnection]
) -> ManagedElementCheckResult:
    """
    Utility to diff two AirbyteConnection objects.
    """
    diff = diff_dicts(
        conn_dict(config_conn),
        conn_dict(curr_conn),
        custom_compare_fn=_compare_stream_values,
    )
    if not diff.is_empty():
        name = config_conn.name if config_conn else curr_conn.name if curr_conn else "Unknown"
        return ManagedElementDiff().with_nested(name, diff)

    return ManagedElementDiff()


def reconcile_sources(
    res: AirbyteResource,
    config_sources: Mapping[str, AirbyteSource],
    existing_sources: Mapping[str, InitializedAirbyteSource],
    workspace_id: str,
    dry_run: bool,
    should_delete: bool,
    ignore_secrets: bool,
) -> Tuple[Mapping[str, InitializedAirbyteSource], ManagedElementCheckResult]:
    """
    Generates a diff of the configured and existing sources and reconciles them to match the
    configured state if dry_run is False.
    """
    diff = ManagedElementDiff()

    initialized_sources: Dict[str, InitializedAirbyteSource] = {}
    for source_name in set(config_sources.keys()).union(existing_sources.keys()):
        configured_source = config_sources.get(source_name)
        existing_source = existing_sources.get(source_name)

        # Ignore sources not mentioned in the user config unless the user specifies to delete
        if not should_delete and existing_source and not configured_source:
            initialized_sources[source_name] = existing_source
            continue

        diff = diff.join(
            diff_sources(
                configured_source,
                existing_source.source if existing_source else None,
                ignore_secrets,
            )
        )

        if existing_source and (
            not configured_source or (configured_source.must_be_recreated(existing_source.source))
        ):
            initialized_sources[source_name] = existing_source
            if not dry_run:
                res.make_request(
                    endpoint="/sources/delete",
                    data={"sourceId": existing_source.source_id},
                )
            existing_source = None

        if configured_source:
            defn_id = check.not_none(
                res.get_source_definition_by_name(configured_source.source_type, workspace_id)
            )
            base_source_defn_dict = {
                "name": configured_source.name,
                "connectionConfiguration": configured_source.source_configuration,
            }
            source_id = ""
            if existing_source:
                source_id = existing_source.source_id
                if not dry_run:
                    res.make_request(
                        endpoint="/sources/update",
                        data={"sourceId": source_id, **base_source_defn_dict},
                    )
            else:
                if not dry_run:
                    create_result = cast(
                        Dict[str, str],
                        check.not_none(
                            res.make_request(
                                endpoint="/sources/create",
                                data={
                                    "sourceDefinitionId": defn_id,
                                    "workspaceId": workspace_id,
                                    **base_source_defn_dict,
                                },
                            )
                        ),
                    )
                    source_id = create_result["sourceId"]

            if source_name in initialized_sources:
                # Preserve to be able to initialize old connection object
                initialized_sources[f"{source_name}_old"] = initialized_sources[source_name]
            initialized_sources[source_name] = InitializedAirbyteSource(
                source=configured_source,
                source_id=source_id,
                source_definition_id=defn_id,
            )
    return initialized_sources, diff


def reconcile_destinations(
    res: AirbyteResource,
    config_destinations: Mapping[str, AirbyteDestination],
    existing_destinations: Mapping[str, InitializedAirbyteDestination],
    workspace_id: str,
    dry_run: bool,
    should_delete: bool,
    ignore_secrets: bool,
) -> Tuple[Mapping[str, InitializedAirbyteDestination], ManagedElementCheckResult]:
    """
    Generates a diff of the configured and existing destinations and reconciles them to match the
    configured state if dry_run is False.
    """
    diff = ManagedElementDiff()

    initialized_destinations: Dict[str, InitializedAirbyteDestination] = {}
    for destination_name in set(config_destinations.keys()).union(existing_destinations.keys()):
        configured_destination = config_destinations.get(destination_name)
        existing_destination = existing_destinations.get(destination_name)

        # Ignore destinations not mentioned in the user config unless the user specifies to delete
        if not should_delete and existing_destination and not configured_destination:
            initialized_destinations[destination_name] = existing_destination
            continue

        diff = diff.join(
            diff_destinations(
                configured_destination,
                existing_destination.destination if existing_destination else None,
                ignore_secrets,
            )
        )

        if existing_destination and (
            not configured_destination
            or (configured_destination.must_be_recreated(existing_destination.destination))
        ):
            initialized_destinations[destination_name] = existing_destination
            if not dry_run:
                res.make_request(
                    endpoint="/destinations/delete",
                    data={"destinationId": existing_destination.destination_id},
                )
            existing_destination = None

        if configured_destination:
            defn_id = res.get_destination_definition_by_name(
                configured_destination.destination_type, workspace_id
            )
            base_destination_defn_dict = {
                "name": configured_destination.name,
                "connectionConfiguration": configured_destination.destination_configuration,
            }
            destination_id = ""
            if existing_destination:
                destination_id = existing_destination.destination_id
                if not dry_run:
                    res.make_request(
                        endpoint="/destinations/update",
                        data={"destinationId": destination_id, **base_destination_defn_dict},
                    )
            else:
                if not dry_run:
                    create_result = cast(
                        Dict[str, str],
                        check.not_none(
                            res.make_request(
                                endpoint="/destinations/create",
                                data={
                                    "destinationDefinitionId": defn_id,
                                    "workspaceId": workspace_id,
                                    **base_destination_defn_dict,
                                },
                            )
                        ),
                    )
                    destination_id = create_result["destinationId"]

            if destination_name in initialized_destinations:
                # Preserve to be able to initialize old connection object
                initialized_destinations[f"{destination_name}_old"] = initialized_destinations[
                    destination_name
                ]
            initialized_destinations[destination_name] = InitializedAirbyteDestination(
                destination=configured_destination,
                destination_id=destination_id,
                destination_definition_id=defn_id,
            )
    return initialized_destinations, diff


def reconcile_config(
    res: AirbyteResource,
    objects: Sequence[AirbyteConnection],
    dry_run: bool = False,
    should_delete: bool = False,
    ignore_secrets: bool = True,
) -> ManagedElementCheckResult:
    """
    Main entry point for the reconciliation process. Takes a list of AirbyteConnection objects
    and a pointer to an Airbyte instance and returns a diff, along with applying the diff
    if dry_run is False.
    """
    with res.cache_requests():
        config_connections = {conn.name: conn for conn in objects}
        config_sources = {conn.source.name: conn.source for conn in objects}
        config_dests = {conn.destination.name: conn.destination for conn in objects}

        workspace_id = res.get_default_workspace()

        existing_sources_raw = cast(
            Dict[str, List[Dict[str, Any]]],
            check.not_none(
                res.make_request(endpoint="/sources/list", data={"workspaceId": workspace_id})
            ),
        )
        existing_dests_raw = cast(
            Dict[str, List[Dict[str, Any]]],
            check.not_none(
                res.make_request(endpoint="/destinations/list", data={"workspaceId": workspace_id})
            ),
        )

        existing_sources: Dict[str, InitializedAirbyteSource] = {
            source_json["name"]: InitializedAirbyteSource.from_api_json(source_json)
            for source_json in existing_sources_raw.get("sources", [])
        }
        existing_dests: Dict[str, InitializedAirbyteDestination] = {
            destination_json["name"]: InitializedAirbyteDestination.from_api_json(destination_json)
            for destination_json in existing_dests_raw.get("destinations", [])
        }

        # First, remove any connections that need to be deleted, so that we can
        # safely delete any sources/destinations that are no longer referenced
        # or that need to be recreated.
        connections_diff = reconcile_connections_pre(
            res,
            config_connections,
            existing_sources,
            existing_dests,
            workspace_id,
            dry_run,
            should_delete,
        )

        all_sources, sources_diff = reconcile_sources(
            res,
            config_sources,
            existing_sources,
            workspace_id,
            dry_run,
            should_delete,
            ignore_secrets,
        )
        all_dests, dests_diff = reconcile_destinations(
            res, config_dests, existing_dests, workspace_id, dry_run, should_delete, ignore_secrets
        )

        # Now that we have updated the set of sources and destinations, we can
        # recreate or update any connections which depend on them.
        reconcile_connections_post(
            res,
            config_connections,
            all_sources,
            all_dests,
            workspace_id,
            dry_run,
        )

        return ManagedElementDiff().join(sources_diff).join(dests_diff).join(connections_diff)


def reconcile_normalization(
    res: AirbyteResource,
    existing_connection_id: Optional[str],
    destination: InitializedAirbyteDestination,
    normalization_config: Optional[bool],
    workspace_id: str,
) -> Optional[str]:
    """
    Reconciles the normalization configuration for a connection.

    If normalization_config is None, then defaults to True on destinations that support normalization
    and False on destinations that do not.
    """
    existing_basic_norm_op_id = None
    if existing_connection_id:
        operations = cast(
            Dict[str, List[Dict[str, str]]],
            check.not_none(
                res.make_request(
                    endpoint="/operations/list",
                    data={"connectionId": existing_connection_id},
                )
            ),
        )
        existing_basic_norm_op = next(
            (
                operation
                for operation in operations["operations"]
                if is_basic_normalization_operation(operation)
            ),
            None,
        )
        existing_basic_norm_op_id = (
            existing_basic_norm_op["operationId"] if existing_basic_norm_op else None
        )

    if normalization_config is not False:
        if destination.destination_definition_id and res.does_dest_support_normalization(
            destination.destination_definition_id, workspace_id
        ):
            if existing_basic_norm_op_id:
                return existing_basic_norm_op_id
            else:
                return cast(
                    Dict[str, str],
                    check.not_none(
                        res.make_request(
                            endpoint="/operations/create",
                            data={
                                "workspaceId": workspace_id,
                                "name": "Normalization",
                                "operatorConfiguration": {
                                    "operatorType": "normalization",
                                    "normalization": {"option": "basic"},
                                },
                            },
                        )
                    ),
                )["operationId"]
        elif normalization_config is True:
            raise Exception(
                f"Destination {destination.destination.name} does not support normalization."
            )

    return None


def reconcile_connections_pre(
    res: AirbyteResource,
    config_connections: Mapping[str, AirbyteConnection],
    existing_sources: Mapping[str, InitializedAirbyteSource],
    existing_destinations: Mapping[str, InitializedAirbyteDestination],
    workspace_id: str,
    dry_run: bool,
    should_delete: bool,
) -> ManagedElementCheckResult:
    """
    Generates the diff for connections, and deletes any connections that are not in the config if
    dry_run is False.

    It's necessary to do this in two steps because we need to remove connections that depend on
    sources and destinations that are being deleted or recreated before Airbyte will allow us to
    delete or recreate them.
    """
    diff = ManagedElementDiff()

    existing_connections_raw = cast(
        Dict[str, List[Dict[str, Any]]],
        check.not_none(
            res.make_request(endpoint="/connections/list", data={"workspaceId": workspace_id})
        ),
    )
    existing_connections: Dict[str, InitializedAirbyteConnection] = {
        connection_json["name"]: InitializedAirbyteConnection.from_api_json(
            connection_json, existing_sources, existing_destinations
        )
        for connection_json in existing_connections_raw.get("connections", [])
    }

    for conn_name in set(config_connections.keys()).union(existing_connections.keys()):
        config_conn = config_connections.get(conn_name)
        existing_conn = existing_connections.get(conn_name)

        # Ignore connections not mentioned in the user config unless the user specifies to delete
        if not should_delete and not config_conn:
            continue

        diff = diff.join(
            diff_connections(config_conn, existing_conn.connection if existing_conn else None)
        )

        if existing_conn and (
            not config_conn or config_conn.must_be_recreated(existing_conn.connection)
        ):
            if not dry_run:
                res.make_request(
                    endpoint="/connections/delete",
                    data={"connectionId": existing_conn.connection_id},
                )
    return diff


def reconcile_connections_post(
    res: AirbyteResource,
    config_connections: Mapping[str, AirbyteConnection],
    init_sources: Mapping[str, InitializedAirbyteSource],
    init_dests: Mapping[str, InitializedAirbyteDestination],
    workspace_id: str,
    dry_run: bool,
) -> None:
    """
    Creates new and modifies existing connections based on the config if dry_run is False.
    """
    existing_connections_raw = cast(
        Dict[str, List[Dict[str, Any]]],
        check.not_none(
            res.make_request(endpoint="/connections/list", data={"workspaceId": workspace_id})
        ),
    )
    existing_connections = {
        connection_json["name"]: InitializedAirbyteConnection.from_api_json(
            connection_json, init_sources, init_dests
        )
        for connection_json in existing_connections_raw.get("connections", [])
    }

    for conn_name, config_conn in config_connections.items():
        existing_conn = existing_connections.get(conn_name)

        normalization_operation_id = None
        if not dry_run:
            destination = init_dests[config_conn.destination.name]

            # Enable or disable basic normalization based on config
            normalization_operation_id = reconcile_normalization(
                res,
                existing_connections.get("name", {}).get("connectionId"),
                destination,
                config_conn.normalize_data,
                workspace_id,
            )

        configured_streams = []
        if not dry_run:
            source = init_sources[config_conn.source.name]
            schema = res.get_source_schema(source.source_id)
            base_streams = schema["catalog"]["streams"]

            configured_streams = [
                gen_configured_stream_json(stream, config_conn.stream_config)
                for stream in base_streams
                if stream["stream"]["name"] in config_conn.stream_config
            ]

        connection_base_json = {
            "name": conn_name,
            "namespaceDefinition": "source",
            "namespaceFormat": "${SOURCE_NAMESPACE}",
            "prefix": "",
            "operationIds": [normalization_operation_id] if normalization_operation_id else [],
            "syncCatalog": {"streams": configured_streams},
            "scheduleType": "manual",
            "status": "active",
        }

        if isinstance(config_conn.destination_namespace, AirbyteDestinationNamespace):
            connection_base_json["namespaceDefinition"] = config_conn.destination_namespace.value
        else:
            connection_base_json["namespaceDefinition"] = "customformat"
            connection_base_json["namespaceFormat"] = cast(str, config_conn.destination_namespace)

        if config_conn.prefix:
            connection_base_json["prefix"] = config_conn.prefix

        if existing_conn:
            if not dry_run:
                source = init_sources[config_conn.source.name]
                res.make_request(
                    endpoint="/connections/update",
                    data={
                        **connection_base_json,
                        "sourceCatalogId": res.get_source_catalog_id(source.source_id),
                        "connectionId": existing_conn.connection_id,
                    },
                )
        else:
            if not dry_run:
                source = init_sources[config_conn.source.name]
                destination = init_dests[config_conn.destination.name]

                res.make_request(
                    endpoint="/connections/create",
                    data={
                        **connection_base_json,
                        "sourceCatalogId": res.get_source_catalog_id(source.source_id),
                        "sourceId": source.source_id,
                        "destinationId": destination.destination_id,
                    },
                )


@experimental
class AirbyteManagedElementReconciler(ManagedElementReconciler):
    """
    Reconciles Python-specified Airbyte connections with an Airbyte instance.

    Passing the module containing an AirbyteManagedElementReconciler to the dagster-airbyte
    CLI will allow you to check the state of your Python-code-specified Airbyte connections
    against an Airbyte instance, and reconcile them if necessary.

    This functionality is experimental and subject to change.
    """

    @public
    def __init__(
        self,
        airbyte: ResourceDefinition,
        connections: Iterable[AirbyteConnection],
        delete_unmentioned_resources: bool = False,
    ):
        """
        Reconciles Python-specified Airbyte connections with an Airbyte instance.

        Args:
            airbyte (ResourceDefinition): The Airbyte resource definition to reconcile against.
            connections (Iterable[AirbyteConnection]): The Airbyte connection objects to reconcile.
            delete_unmentioned_resources (bool): Whether to delete resources that are not mentioned in
                the set of connections provided. When True, all Airbyte instance contents are effectively
                managed by the reconciler. Defaults to False.
        """
        airbyte = check.inst_param(airbyte, "airbyte", ResourceDefinition)

        self._airbyte_instance: AirbyteResource = airbyte(build_init_resource_context())
        self._connections = list(
            check.iterable_param(connections, "connections", of_type=AirbyteConnection)
        )
        self._delete_unmentioned_resources = check.bool_param(
            delete_unmentioned_resources, "delete_unmentioned_resources"
        )

        super().__init__()

    def check(self, **kwargs) -> ManagedElementCheckResult:
        return reconcile_config(
            self._airbyte_instance,
            self._connections,
            dry_run=True,
            should_delete=self._delete_unmentioned_resources,
            ignore_secrets=(not kwargs.get("include_all_secrets", False)),
        )

    def apply(self, **kwargs) -> ManagedElementCheckResult:
        return reconcile_config(
            self._airbyte_instance,
            self._connections,
            dry_run=False,
            should_delete=self._delete_unmentioned_resources,
            ignore_secrets=(not kwargs.get("include_all_secrets", False)),
        )


class AirbyteManagedElementCacheableAssetsDefinition(AirbyteInstanceCacheableAssetsDefinition):
    def __init__(
        self,
        airbyte_resource_def: ResourceDefinition,
        key_prefix: Sequence[str],
        create_assets_for_normalization_tables: bool,
        connection_to_group_fn: Optional[Callable[[str], Optional[str]]],
        connections: Iterable[AirbyteConnection],
        connection_to_io_manager_key_fn: Optional[Callable[[str], Optional[str]]],
        connection_to_asset_key_fn: Optional[Callable[[AirbyteConnectionMetadata, str], AssetKey]],
        connection_to_freshness_policy_fn: Optional[
            Callable[[AirbyteConnectionMetadata], Optional[FreshnessPolicy]]
        ],
    ):
        defined_conn_names = {conn.name for conn in connections}
        super().__init__(
            airbyte_resource_def=airbyte_resource_def,
            workspace_id=None,
            key_prefix=key_prefix,
            create_assets_for_normalization_tables=create_assets_for_normalization_tables,
            connection_to_group_fn=connection_to_group_fn,
            connection_to_io_manager_key_fn=connection_to_io_manager_key_fn,
            connection_filter=lambda conn: conn.name in defined_conn_names,
            connection_to_asset_key_fn=connection_to_asset_key_fn,
            connection_to_freshness_policy_fn=connection_to_freshness_policy_fn,
        )
        self._connections: List[AirbyteConnection] = list(connections)

    def _get_connections(self) -> Sequence[Tuple[str, AirbyteConnectionMetadata]]:
        diff = reconcile_config(self._airbyte_instance, self._connections, dry_run=True)
        if isinstance(diff, ManagedElementDiff) and not diff.is_empty():
            raise ValueError(
                "Airbyte connections are not in sync with provided configuration, diff:\n{}".format(
                    str(diff)
                )
            )
        elif isinstance(diff, ManagedElementError):
            raise ValueError("Error checking Airbyte connections: {}".format(str(diff)))

        return super()._get_connections()


@experimental
def load_assets_from_connections(
    airbyte: ResourceDefinition,
    connections: Iterable[AirbyteConnection],
    key_prefix: Optional[CoercibleToAssetKeyPrefix] = None,
    create_assets_for_normalization_tables: bool = True,
    connection_to_group_fn: Optional[Callable[[str], Optional[str]]] = _clean_name,
    io_manager_key: Optional[str] = None,
    connection_to_io_manager_key_fn: Optional[Callable[[str], Optional[str]]] = None,
    connection_to_asset_key_fn: Optional[
        Callable[[AirbyteConnectionMetadata, str], AssetKey]
    ] = None,
    connection_to_freshness_policy_fn: Optional[
        Callable[[AirbyteConnectionMetadata], Optional[FreshnessPolicy]]
    ] = None,
) -> CacheableAssetsDefinition:
    """
    Loads Airbyte connection assets from a configured AirbyteResource instance, checking against a list of AirbyteConnection objects.
    This method will raise an error on repo load if the passed AirbyteConnection objects are not in sync with the Airbyte instance.

    Args:
        airbyte (ResourceDefinition): An AirbyteResource configured with the appropriate connection
            details.
        connections (Iterable[AirbyteConnection]): A list of AirbyteConnection objects to build assets for.
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
        connection_to_asset_key_fn (Optional[Callable[[AirbyteConnectionMetadata, str], AssetKey]]): Optional function which
            takes in connection metadata and table name and returns an asset key for the table. If None, the default asset
            key is based on the table name. Any asset key prefix will be applied to the output of this function.
        connection_to_freshness_policy_fn (Optional[Callable[[AirbyteConnectionMetadata], Optional[FreshnessPolicy]]]): Optional function which
            takes in connection metadata and returns a freshness policy for the connection. If None, no freshness policy will be applied.

    **Examples:**

    .. code-block:: python

        from dagster_airbyte import (
            AirbyteConnection,
            airbyte_resource,
            load_assets_from_connections,
        )

        airbyte_instance = airbyte_resource.configured(
            {
                "host": "localhost",
                "port": "8000",
            }
        )
        airbyte_connections = [
            AirbyteConnection(...),
            AirbyteConnection(...)
        ]
        airbyte_assets = load_assets_from_connections(airbyte_instance, airbyte_connections)
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

    return AirbyteManagedElementCacheableAssetsDefinition(
        airbyte_resource_def=check.inst_param(airbyte, "airbyte", ResourceDefinition),
        key_prefix=key_prefix,
        create_assets_for_normalization_tables=check.bool_param(
            create_assets_for_normalization_tables, "create_assets_for_normalization_tables"
        ),
        connection_to_group_fn=check.opt_callable_param(
            connection_to_group_fn, "connection_to_group_fn"
        ),
        connection_to_io_manager_key_fn=connection_to_io_manager_key_fn,
        connections=check.iterable_param(connections, "connections", of_type=AirbyteConnection),
        connection_to_asset_key_fn=connection_to_asset_key_fn,
        connection_to_freshness_policy_fn=connection_to_freshness_policy_fn,
    )
