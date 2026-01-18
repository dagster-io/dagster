import json
from collections.abc import Iterable, Mapping
from itertools import chain
from typing import Any, Optional

import dagster._check as check
from dagster import ResourceDefinition
from dagster._annotations import beta, deprecated
from dagster._core.execution.context.init import build_init_resource_context
from dagster_managed_elements import ManagedElementCheckResult, ManagedElementDiff
from dagster_managed_elements.types import ManagedElementReconciler, is_key_secret
from dagster_managed_elements.utils import diff_dicts

from dagster_fivetran import FivetranResource
from dagster_fivetran.managed.types import (
    MANAGED_ELEMENTS_DEPRECATION_MSG,
    FivetranConnector,
    FivetranDestination,
    InitializedFivetranConnector,
    InitializedFivetranDestination,
)

FIVETRAN_SECRET_MASK = "******"


def _ignore_secrets_compare_fn(k: str, _cv: Any, dv: Any) -> Optional[bool]:
    if is_key_secret(k):
        return dv == FIVETRAN_SECRET_MASK
    return None


def _diff_configs(
    config_dict: dict[str, Any], dst_dict: dict[str, Any], ignore_secrets: bool = True
) -> ManagedElementDiff:
    return diff_dicts(
        config_dict=config_dict,
        dst_dict=dst_dict,
        custom_compare_fn=_ignore_secrets_compare_fn if ignore_secrets else None,
    )


def diff_destinations(
    config_dst: Optional[FivetranDestination],
    curr_dst: Optional[FivetranDestination],
    ignore_secrets: bool = True,
) -> ManagedElementCheckResult:
    """Utility to diff two FivetranDestination objects."""
    diff = _diff_configs(
        config_dst.destination_configuration if config_dst else {},
        curr_dst.destination_configuration if curr_dst else {},
        ignore_secrets,
    )
    if not diff.is_empty():
        name = config_dst.name if config_dst else curr_dst.name if curr_dst else "Unknown"
        return ManagedElementDiff().with_nested(name, diff)

    return ManagedElementDiff()


def diff_connectors(
    config_conn: Optional[FivetranConnector],
    curr_conn: Optional[FivetranConnector],
    ignore_secrets: bool = True,
) -> ManagedElementCheckResult:
    """Utility to diff two FivetranDestination objects."""
    diff = _diff_configs(
        config_conn.source_configuration if config_conn else {},
        curr_conn.source_configuration if curr_conn else {},
        ignore_secrets,
    )
    if not diff.is_empty():
        name = (
            config_conn.schema_name
            if config_conn
            else curr_conn.schema_name
            if curr_conn
            else "Unknown"
        )
        return ManagedElementDiff().with_nested(name, diff)

    return ManagedElementDiff()


def reconcile_connectors(
    res: FivetranResource,
    config_connectors: Mapping[str, FivetranConnector],
    existing_connectors: Mapping[str, InitializedFivetranConnector],
    all_destinations: Mapping[str, InitializedFivetranDestination],
    dry_run: bool,
    should_delete: bool,
    ignore_secrets: bool,
) -> ManagedElementCheckResult:
    diff = ManagedElementDiff()

    for connector_name in set(config_connectors.keys()).union(existing_connectors.keys()):
        configured_connector = config_connectors.get(connector_name)
        existing_connector = existing_connectors.get(connector_name)

        # Ignore connectors not mentioned in the user config unless the user specifies to delete
        if not should_delete and existing_connector and not configured_connector:
            continue

        diff = diff.join(
            diff_connectors(  # type: ignore
                configured_connector,
                existing_connector.connector if existing_connector else None,
                ignore_secrets,
            )
        )

        if existing_connector and (
            not configured_connector
            or (configured_connector.must_be_recreated(existing_connector.connector))
        ):
            if not dry_run:
                res.make_request(
                    method="DELETE",
                    endpoint=f"connectors/{existing_connector.connector_id}",
                )
            existing_connector = None

        if configured_connector:
            dest_name = check.not_none(configured_connector.destination).name
            group_id = all_destinations[dest_name].destination_id
            config = {
                **configured_connector.source_configuration,
                "schema": configured_connector.schema_name,
            }
            base_connector_dict = {
                "schedule_type": "MANUAL",
                "config": config,
                "auth": configured_connector.auth_configuration,
            }
            if not dry_run:
                if existing_connector:
                    connector_id = existing_connector.connector_id
                    if not dry_run:
                        res.make_request(
                            method="PATCH",
                            endpoint=f"connectors/{connector_id}",
                            data=json.dumps(base_connector_dict),
                        )
                else:
                    if not dry_run:
                        res.make_request(
                            method="POST",
                            endpoint="connectors",
                            data=json.dumps(
                                {
                                    "service": configured_connector.source_type,
                                    "group_id": group_id,
                                    **base_connector_dict,
                                }
                            ),
                        )

    return diff


def reconcile_destinations(
    res: FivetranResource,
    config_destinations: Mapping[str, FivetranDestination],
    existing_destinations: Mapping[str, InitializedFivetranDestination],
    dry_run: bool,
    should_delete: bool,
    ignore_secrets: bool,
) -> tuple[Mapping[str, InitializedFivetranDestination], ManagedElementCheckResult]:
    """Generates a diff of the configured and existing destinations and reconciles them to match the
    configured state if dry_run is False.
    """
    diff = ManagedElementDiff()

    initialized_destinations: dict[str, InitializedFivetranDestination] = {}
    for destination_name in set(config_destinations.keys()).union(existing_destinations.keys()):
        configured_destination = config_destinations.get(destination_name)
        existing_destination = existing_destinations.get(destination_name)

        # Ignore destinations not mentioned in the user config unless the user specifies to delete
        if not should_delete and existing_destination and not configured_destination:
            initialized_destinations[destination_name] = existing_destination
            continue

        diff = diff.join(
            diff_destinations(  # type: ignore
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
                connectors = [
                    conn["id"]
                    for conn in res.make_request(
                        "GET", f"groups/{existing_destination.destination_id}/connectors"
                    )["items"]
                ]
                for connector_id in connectors:
                    res.make_request(
                        method="DELETE",
                        endpoint=f"connectors/{connector_id}",
                    )
                res.make_request(
                    method="DELETE",
                    endpoint=f"destinations/{existing_destination.destination_id}",
                )
                res.make_request(
                    method="DELETE",
                    endpoint=f"groups/{existing_destination.destination_id}",
                )
            existing_destination = None

        if configured_destination:
            base_destination_dict = {
                "region": configured_destination.region,
                "time_zone_offset": configured_destination.time_zone_offset,
                "config": configured_destination.destination_configuration,
            }
            destination_id = "TBD"
            if not dry_run:
                if existing_destination:
                    destination_id = existing_destination.destination_id
                    if not dry_run:
                        res.make_request(
                            method="PATCH",
                            endpoint=f"destinations/{destination_id}",
                            data=json.dumps(base_destination_dict),
                        )
                else:
                    if not dry_run:
                        group_res = res.make_request(
                            method="POST",
                            endpoint="groups",
                            data=json.dumps(
                                {
                                    "name": configured_destination.name,
                                }
                            ),
                        )
                        destination_id = group_res["id"]

                        res.make_request(
                            method="POST",
                            endpoint="destinations",
                            data=json.dumps(
                                {
                                    "group_id": destination_id,
                                    "service": configured_destination.destination_type,
                                    **base_destination_dict,
                                }
                            ),
                        )

            initialized_destinations[destination_name] = InitializedFivetranDestination(
                destination=configured_destination,
                destination_id=destination_id,
            )
    return initialized_destinations, diff


def get_connectors_for_group(res: FivetranResource, group_id: str) -> list[dict[str, Any]]:
    connector_ids = {
        conn["id"] for conn in res.make_request("GET", f"groups/{group_id}/connectors")["items"]
    }
    connectors = [
        dict(res.make_request("GET", f"connectors/{connector_id}"))
        for connector_id in connector_ids
    ]
    return connectors


def reconcile_config(
    res: FivetranResource,
    objects: list[FivetranConnector],
    dry_run: bool = False,
    should_delete: bool = False,
    ignore_secrets: bool = True,
) -> ManagedElementCheckResult:
    """Main entry point for the reconciliation process. Takes a list of FivetranConnection objects
    and a pointer to an Fivetran instance and returns a diff, along with applying the diff
    if dry_run is False.
    """
    config_dests_list = [
        check.not_none(conn.destination, "Connections must specify a destination")
        for conn in objects
    ]
    config_dests = {dest.name: dest for dest in config_dests_list}
    config_connectors = {conn.schema_name: conn for conn in objects}

    existing_groups = res.make_request("GET", "groups")["items"]
    existing_dests_raw = {
        group["name"]: dict(res.make_request("GET", f"destinations/{group['id']}"))
        for group in existing_groups
    }
    existing_dests: dict[str, InitializedFivetranDestination] = {
        dest_name: InitializedFivetranDestination.from_api_json(dest_name, dest_json)
        for dest_name, dest_json in existing_dests_raw.items()
    }

    existing_connectors_raw = list(
        chain.from_iterable(get_connectors_for_group(res, group["id"]) for group in existing_groups)
    )
    existing_connectors_list = [
        InitializedFivetranConnector.from_api_json(conn) for conn in existing_connectors_raw
    ]
    existing_connectors = {conn.connector.schema_name: conn for conn in existing_connectors_list}

    all_dests, dests_diff = reconcile_destinations(
        res,
        config_dests,
        existing_dests,
        dry_run,
        should_delete,
        ignore_secrets,
    )

    connectors_diff = reconcile_connectors(
        res,
        config_connectors,
        existing_connectors,
        all_dests,
        dry_run,
        should_delete,
        ignore_secrets,
    )

    return ManagedElementDiff().join(dests_diff).join(connectors_diff)  # type: ignore


@beta
@deprecated(breaking_version="2.0", additional_warn_text=MANAGED_ELEMENTS_DEPRECATION_MSG)
class FivetranManagedElementReconciler(ManagedElementReconciler):
    def __init__(
        self,
        fivetran: ResourceDefinition,
        connectors: Iterable[FivetranConnector],
        delete_unmentioned_resources: bool = False,
    ):
        """Reconciles Python-specified Fivetran resources with an Fivetran instance.

        Args:
            fivetran (ResourceDefinition): The Fivetran resource definition to reconcile against.
            connectors (Iterable[FivetranConnector]): The Fivetran connector objects to reconcile.
            delete_unmentioned_resources (bool): Whether to delete resources that are not mentioned in
                the set of connectors provided. When True, all Fivetran instance contents are effectively
                managed by the reconciler. Defaults to False.
        """
        fivetran = check.inst_param(fivetran, "fivetran", ResourceDefinition)

        self._fivetran_instance: FivetranResource = fivetran(build_init_resource_context())
        self._connectors = list(
            check.iterable_param(connectors, "connectors", of_type=FivetranConnector)
        )
        self._delete_unmentioned_resources = check.bool_param(
            delete_unmentioned_resources, "delete_unmentioned_resources"
        )

        super().__init__()

    def check(self, **kwargs) -> ManagedElementCheckResult:
        return reconcile_config(
            self._fivetran_instance,
            self._connectors,
            dry_run=True,
            should_delete=self._delete_unmentioned_resources,
            ignore_secrets=(not kwargs.get("include_all_secrets", False)),
        )

    def apply(self, **kwargs) -> ManagedElementCheckResult:
        return reconcile_config(
            self._fivetran_instance,
            self._connectors,
            dry_run=False,
            should_delete=self._delete_unmentioned_resources,
            ignore_secrets=(not kwargs.get("include_all_secrets", False)),
        )
