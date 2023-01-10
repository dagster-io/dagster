import json
import re
from contextlib import AbstractContextManager
from typing import Any, Dict, List, Tuple, cast

import responses
from dagster_fivetran import (
    FivetranConnector,
    FivetranDestination,
    FivetranManagedElementReconciler,
    fivetran_resource,
)
from dagster_fivetran.managed.types import (
    InitializedFivetranConnector,
    InitializedFivetranDestination,
)
from dagster_managed_elements.types import ManagedElementDiff
from dagster_managed_elements.utils import diff_dicts
from requests import PreparedRequest


def ok(contents: Dict[str, Any]) -> Any:
    return (200, {}, json.dumps(contents))


def format_callback(callback):
    def wrapper(request: PreparedRequest):
        return ok(
            callback(
                request.method, request.url, json.loads(request.body) if request.body else None
            )
        )

    return wrapper


class MockFivetran(AbstractContextManager):
    def __init__(
        self, connectors: Dict[str, FivetranConnector], destinations: Dict[str, FivetranDestination]
    ):
        self.rsps = responses.RequestsMock(assert_all_requests_are_fired=False)
        self.connectors = connectors
        self.destinations = destinations
        self.created_groups: Dict[str, str] = {}
        self.group_id = 1
        self.connectors_by_destination = {
            dest_id: [
                conn_id
                for conn_id, conn in connectors.items()
                if cast(FivetranDestination, conn.destination).name == dest.name
            ]
            for dest_id, dest in destinations.items()
        }
        self.operations_log: List[Tuple[str, str]] = []

    def __enter__(self):
        self.rsps.__enter__()
        self.rsps.add_callback(
            responses.GET,
            "https://api.fivetran.com/v1/groups",
            callback=format_callback(self.mock_groups),
        )
        self.rsps.add_callback(
            responses.GET,
            re.compile(r"https://api.fivetran.com/v1/destinations/.*"),
            callback=format_callback(self.mock_destination),
        )
        self.rsps.add_callback(
            responses.GET,
            re.compile(r"https://api.fivetran.com/v1/groups/.*/connectors"),
            callback=format_callback(self.mock_connectors),
        )
        self.rsps.add_callback(
            responses.GET,
            re.compile(r"https://api.fivetran.com/v1/connectors/.*"),
            callback=format_callback(self.mock_connector),
        )

        self.rsps.add_callback(
            responses.PATCH,
            re.compile(r"https://api.fivetran.com/v1/destinations/.*"),
            callback=format_callback(self.mock_patch_destination),
        )
        self.rsps.add_callback(
            responses.PATCH,
            re.compile(r"https://api.fivetran.com/v1/connectors/.*"),
            callback=format_callback(self.mock_patch_connector),
        )

        self.rsps.add_callback(
            responses.POST,
            "https://api.fivetran.com/v1/groups",
            callback=format_callback(self.mock_post_groups),
        )
        self.rsps.add_callback(
            responses.POST,
            "https://api.fivetran.com/v1/destinations",
            callback=format_callback(self.mock_post_destinations),
        )
        self.rsps.add_callback(
            responses.POST,
            "https://api.fivetran.com/v1/connectors",
            callback=format_callback(self.mock_post_connectors),
        )

        return self

    def mock_post_groups(self, _method, _url, contents):
        self.operations_log.append(("post_groups", contents["name"]))

        new_group_id = str(self.group_id)
        self.created_groups[new_group_id] = contents["name"]
        self.group_id += 1
        return {"code": "Success", "data": {"id": new_group_id}}

    def mock_post_destinations(self, _method, _url, contents):
        group_id = contents["group_id"]
        self.operations_log.append(("post_destinations", group_id))

        self.destinations[group_id] = InitializedFivetranDestination.from_api_json(
            name=self.created_groups[group_id], api_json={**contents, "id": "my_new_dest_id"}
        ).destination
        self.connectors_by_destination[group_id] = []
        return {"code": "Success"}

    def mock_post_connectors(self, _method, _url, contents):
        group_id = contents["group_id"]
        self.operations_log.append(("post_connectors", group_id))

        conn = InitializedFivetranConnector.from_api_json(
            api_json={**contents, "id": "my_new_conn_id", "schema": contents["config"]["schema"]}
        ).connector
        conn.destination = self.destinations[group_id]
        self.connectors["my_new_conn_id"] = conn

        self.connectors_by_destination[group_id].append("my_new_conn_id")

        return {"code": "Success"}

    def mock_patch_destination(self, _method, url, contents):
        destination_id = url.split("/")[-1]
        destination = self.destinations[destination_id]
        destination.destination_configuration = contents["config"]

        self.operations_log.append(("patch_destination", destination_id))

        return {"code": "Success"}

    def mock_patch_connector(self, _method, url, contents):
        connector_id = url.split("/")[-1]
        connector = self.connectors[connector_id]
        connector.source_configuration = contents["config"]

        self.operations_log.append(("patch_connector", connector_id))

        return {"code": "Success"}

    def mock_connector(self, _method, url, _contents):
        connector_id = url.split("/")[-1]
        connector = self.connectors[connector_id]
        return {
            "code": "Success",
            "data": {
                "id": connector_id,
                "group_id": connector.destination.name,
                "service": connector.source_type,
                "service_version": 1,
                "schema": connector.schema_name,
                "connected_by": "concerning_batch",
                "created_at": "2018-07-21T22:55:21.724201Z",
                "succeeded_at": "2018-12-26T17:58:18.245Z",
                "failed_at": "2018-08-24T15:24:58.872491Z",
                "sync_frequency": 60,
                "status": {
                    "setup_state": "connected",
                    "sync_state": "paused",
                    "update_state": "delayed",
                    "is_historical_sync": False,
                    "tasks": [],
                    "warnings": [],
                },
                "config": connector.source_configuration,
            },
        }

    def mock_connectors(self, _method, url, _contents):
        destination_id = url.split("/")[-2]
        connector_ids = self.connectors_by_destination[destination_id]
        connectors = {conn_id: self.connectors[conn_id] for conn_id in connector_ids}

        return {
            "code": "Success",
            "data": {
                "items": [
                    {
                        "id": conn_id,
                        "group_id": destination_id,
                        "service": conn.source_type,
                        "service_version": 1,
                        "schema": conn.schema_name,
                        "connected_by": "concerning_batch",
                        "created_at": "2018-07-21T22:55:21.724201Z",
                        "succeeded_at": "2018-12-26T17:58:18.245Z",
                        "failed_at": "2018-08-24T15:24:58.872491Z",
                        "sync_frequency": 60,
                        "status": {
                            "setup_state": "connected",
                            "sync_state": "paused",
                            "update_state": "delayed",
                            "is_historical_sync": False,
                            "tasks": [],
                            "warnings": [],
                        },
                    }
                    for conn_id, conn in connectors.items()
                ],
                "next_cursor": "eyJza2lwIjoxfQ",
            },
        }

    def mock_destination(self, _method, url, _contents):
        destination_id = url.split("/")[-1]
        destination = self.destinations[destination_id]

        return {
            "code": "Success",
            "data": {
                "id": destination_id,
                "group_id": destination_id,
                "service": destination.destination_type,
                "region": destination.region,
                "time_zone_offset": destination.time_zone_offset,
                "setup_status": "connected",
                "config": destination.destination_configuration,
            },
        }

    def mock_groups(self, _method, _url, _contents):
        return {
            "items": [
                {
                    "id": dest_id,
                    "name": dest.name,
                }
                for dest_id, dest in self.destinations.items()
            ]
        }

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rsps.__exit__(exc_type, exc_val, exc_tb)


def add_groups_response(res: responses.RequestsMock, groups: List[Tuple[str, str]]):
    res.add(
        responses.GET,
        "https://api.fivetran.com/v1/groups",
        json={
            "items": [
                {
                    "id": group_id,
                    "name": group_name,
                }
                for group_id, group_name in groups
            ]
        },
    )


def add_groups_destinations(
    res: responses.RequestsMock, dest_id: str, destination: FivetranDestination
):
    res.add(
        responses.GET,
        f"https://api.fivetran.com/v1/destinations/{dest_id}",
        json={
            "code": "Success",
            "data": {
                "id": dest_id,
                "group_id": dest_id,
                "service": destination.destination_type,
                "region": destination.region,
                "time_zone_offset": destination.time_zone_offset,
                "setup_status": "connected",
                "config": destination.destination_configuration,
            },
        },
    )


def add_groups_connectors(
    res: responses.RequestsMock, group_id: str, connectors: Dict[str, FivetranConnector]
):
    res.add(
        responses.GET,
        f"https://api.fivetran.com/v1/groups/{group_id}/connectors",
        json={
            "code": "Success",
            "data": {
                "items": [
                    {
                        "id": conn_id,
                        "group_id": group_id,
                        "service": conn.source_type,
                        "service_version": 1,
                        "schema": conn.schema_name,
                        "connected_by": "concerning_batch",
                        "created_at": "2018-07-21T22:55:21.724201Z",
                        "succeeded_at": "2018-12-26T17:58:18.245Z",
                        "failed_at": "2018-08-24T15:24:58.872491Z",
                        "sync_frequency": 60,
                        "status": {
                            "setup_state": "connected",
                            "sync_state": "paused",
                            "update_state": "delayed",
                            "is_historical_sync": False,
                            "tasks": [],
                            "warnings": [],
                        },
                    }
                    for conn_id, conn in connectors.items()
                ],
                "next_cursor": "eyJza2lwIjoxfQ",
            },
        },
    )

    for conn_id, conn in connectors.items():
        res.add(
            responses.GET,
            f"https://api.fivetran.com/v1/connectors/{conn_id}",
            json={
                "code": "Success",
                "data": {
                    "id": conn_id,
                    "group_id": group_id,
                    "service": conn.source_type,
                    "service_version": 1,
                    "schema": conn.schema_name,
                    "connected_by": "concerning_batch",
                    "created_at": "2018-07-21T22:55:21.724201Z",
                    "succeeded_at": "2018-12-26T17:58:18.245Z",
                    "failed_at": "2018-08-24T15:24:58.872491Z",
                    "sync_frequency": 60,
                    "status": {
                        "setup_state": "connected",
                        "sync_state": "paused",
                        "update_state": "delayed",
                        "is_historical_sync": False,
                        "tasks": [],
                        "warnings": [],
                    },
                    "config": conn.source_configuration,
                },
            },
        )


@responses.activate
def test_basic_end_to_end():
    ft_instance = fivetran_resource.configured(
        {
            "api_key": "some_key",
            "api_secret": "some_secret",
        }
    )

    snowflake_destination = FivetranDestination(
        name="my_destination",
        destination_type="Snowflake",
        region="GCP_US_EAST4",
        time_zone_offset=0,
        destination_configuration={
            "baz": "qux",
        },
    )

    github_conn = FivetranConnector(
        schema_name="my_connector",
        source_type="GitHub",
        source_configuration={
            "foo": "bar",
        },
        destination=snowflake_destination,
    )

    reconciler = FivetranManagedElementReconciler(
        fivetran=ft_instance,
        connectors=[github_conn],
    )

    with MockFivetran(
        connectors={"my_connector": github_conn},
        destinations={"my_destination": snowflake_destination},
    ) as mock_ft:
        assert reconciler.check() == ManagedElementDiff()
        assert reconciler.apply() == ManagedElementDiff()

        assert mock_ft.operations_log == [
            ("patch_destination", "my_destination"),
            ("patch_connector", "my_connector"),
        ]

    with MockFivetran(
        connectors={},
        destinations={},
    ) as mock_ft:
        expected_diff = diff_dicts(
            {
                "my_destination": {"baz": "qux"},
                "my_connector": {"schema": "my_connector", "foo": "bar"},
            },
            {},
        )

        assert reconciler.check() == expected_diff
        assert reconciler.apply() == expected_diff

        assert mock_ft.operations_log == [
            ("post_groups", "my_destination"),
            ("post_destinations", "1"),
            ("post_connectors", "1"),
        ]

        assert reconciler.check() == ManagedElementDiff()
        assert reconciler.apply() == ManagedElementDiff()

        assert mock_ft.operations_log[-2:] == [
            ("patch_destination", "1"),
            ("patch_connector", "my_new_conn_id"),
        ]
