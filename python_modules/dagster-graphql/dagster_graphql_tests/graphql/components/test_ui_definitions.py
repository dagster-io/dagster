"""End-to-end GraphQL tests for the UI definitions endpoints."""

import tempfile
from collections.abc import Iterator
from contextlib import contextmanager

from dagster import Definitions
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.test_utils import instance_for_test
from dagster._core.workspace.context import WorkspaceRequestContext
from dagster_graphql.test.utils import define_out_of_process_context, execute_dagster_graphql

LOCATION_NAME = "test_location"


GET_UI_COMPONENTS_QUERY = """
query GetUIComponents($locationName: String!) {
  uiComponentsForLocationOrError(locationName: $locationName) {
    __typename
    ... on UIComponents {
      locationName
      components {
        componentId
        componentType
        attributes
      }
    }
    ... on PythonError {
      message
    }
  }
}
"""

SET_UI_COMPONENT_MUTATION = """
mutation SetUIComponent(
  $locationName: String!,
  $componentId: String!,
  $componentType: String!,
  $attributes: String!,
) {
  setUIComponent(
    locationName: $locationName,
    componentId: $componentId,
    componentType: $componentType,
    attributes: $attributes,
  ) {
    __typename
    ... on SetUIComponentSuccess {
      component {
        componentId
        componentType
        attributes
      }
    }
    ... on UnauthorizedError {
      message
    }
    ... on PythonError {
      message
    }
  }
}
"""

DELETE_UI_COMPONENT_MUTATION = """
mutation DeleteUIComponent($locationName: String!, $componentId: String!) {
  deleteUIComponent(locationName: $locationName, componentId: $componentId) {
    __typename
    ... on DeleteUIComponentSuccess {
      locationName
      componentId
    }
    ... on UnauthorizedError {
      message
    }
    ... on PythonError {
      message
    }
  }
}
"""


def get_empty_repo() -> RepositoryDefinition:
    return Definitions().get_repository_def()


@contextmanager
def graphql_context_with_storage(
    read_only: bool = False,
) -> Iterator[WorkspaceRequestContext]:
    with tempfile.TemporaryDirectory() as state_dir:
        with instance_for_test(
            overrides={
                "defs_state_storage": {
                    "module": "dagster._core.storage.defs_state.blob_storage_state_storage",
                    "class": "UPathDefsStateStorage",
                    "config": {"base_path": state_dir},
                }
            }
        ) as instance:
            with define_out_of_process_context(
                __file__, "get_empty_repo", instance, read_only=read_only
            ) as context:
                yield context


def _set_component(
    context: WorkspaceRequestContext,
    component_id: str,
    component_type: str = "dagster.SomeComponent",
    attributes: str | None = None,
    location_name: str = LOCATION_NAME,
):
    return execute_dagster_graphql(
        context,
        SET_UI_COMPONENT_MUTATION,
        variables={
            "locationName": location_name,
            "componentId": component_id,
            "componentType": component_type,
            "attributes": attributes if attributes is not None else f"name: {component_id}\n",
        },
    )


def _list_components(context: WorkspaceRequestContext, location_name: str = LOCATION_NAME):
    return execute_dagster_graphql(
        context,
        GET_UI_COMPONENTS_QUERY,
        variables={"locationName": location_name},
    )


def _delete_component(
    context: WorkspaceRequestContext,
    component_id: str,
    location_name: str = LOCATION_NAME,
):
    return execute_dagster_graphql(
        context,
        DELETE_UI_COMPONENT_MUTATION,
        variables={"locationName": location_name, "componentId": component_id},
    )


def test_query_empty():
    with graphql_context_with_storage() as context:
        result = _list_components(context)
        payload = result.data["uiComponentsForLocationOrError"]
        assert payload["__typename"] == "UIComponents"
        assert payload["locationName"] == LOCATION_NAME
        assert payload["components"] == []


def test_set_then_query():
    yaml_attributes = "name: alice\nsettings:\n  enabled: true\n"
    with graphql_context_with_storage() as context:
        set_result = _set_component(
            context,
            component_id="comp1",
            component_type="dagster.SomeComponent",
            attributes=yaml_attributes,
        )
        success = set_result.data["setUIComponent"]
        assert success["__typename"] == "SetUIComponentSuccess"
        assert success["component"]["componentId"] == "comp1"
        assert success["component"]["componentType"] == "dagster.SomeComponent"
        assert success["component"]["attributes"] == yaml_attributes

        list_result = _list_components(context)
        payload = list_result.data["uiComponentsForLocationOrError"]
        assert payload["__typename"] == "UIComponents"
        assert payload["components"] == [
            {
                "componentId": "comp1",
                "componentType": "dagster.SomeComponent",
                "attributes": yaml_attributes,
            }
        ]


def test_set_overwrites_existing_lww():
    """SetUIComponent on an existing id is an upsert (last writer wins)."""
    with graphql_context_with_storage() as context:
        _set_component(context, "comp1", attributes="version: 1\n")
        _set_component(
            context, "comp1", component_type="dagster.OtherComponent", attributes="version: 2\n"
        )
        list_result = _list_components(context)
        components = list_result.data["uiComponentsForLocationOrError"]["components"]
        assert components == [
            {
                "componentId": "comp1",
                "componentType": "dagster.OtherComponent",
                "attributes": "version: 2\n",
            }
        ]


def test_set_multiple_components_returned_sorted():
    with graphql_context_with_storage() as context:
        _set_component(context, "zebra")
        _set_component(context, "alpha")
        _set_component(context, "mango")
        list_result = _list_components(context)
        ids = [
            c["componentId"]
            for c in list_result.data["uiComponentsForLocationOrError"]["components"]
        ]
        assert ids == ["alpha", "mango", "zebra"]


def test_delete_removes_component():
    with graphql_context_with_storage() as context:
        _set_component(context, "comp1")
        _set_component(context, "comp2")

        delete_result = _delete_component(context, "comp1")
        success = delete_result.data["deleteUIComponent"]
        assert success["__typename"] == "DeleteUIComponentSuccess"
        assert success["componentId"] == "comp1"
        assert success["locationName"] == LOCATION_NAME

        list_result = _list_components(context)
        ids = [
            c["componentId"]
            for c in list_result.data["uiComponentsForLocationOrError"]["components"]
        ]
        assert ids == ["comp2"]


def test_delete_is_idempotent():
    """Deleting a non-existent component succeeds quietly."""
    with graphql_context_with_storage() as context:
        delete_result = _delete_component(context, "never-existed")
        assert delete_result.data["deleteUIComponent"]["__typename"] == "DeleteUIComponentSuccess"

        _set_component(context, "comp1")
        _delete_component(context, "comp1")
        # Second delete is also a no-op success.
        delete_result = _delete_component(context, "comp1")
        assert delete_result.data["deleteUIComponent"]["__typename"] == "DeleteUIComponentSuccess"

        list_result = _list_components(context)
        assert list_result.data["uiComponentsForLocationOrError"]["components"] == []


def test_locations_are_isolated():
    """Same component id under different locations does not collide."""
    with graphql_context_with_storage() as context:
        _set_component(context, "shared", attributes="loc: A\n", location_name="locA")
        _set_component(context, "shared", attributes="loc: B\n", location_name="locB")
        _set_component(context, "only_in_a", attributes="loc: A\n", location_name="locA")

        loc_a = _list_components(context, location_name="locA").data[
            "uiComponentsForLocationOrError"
        ]
        loc_b = _list_components(context, location_name="locB").data[
            "uiComponentsForLocationOrError"
        ]

        assert sorted(c["componentId"] for c in loc_a["components"]) == [
            "only_in_a",
            "shared",
        ]
        assert [c["componentId"] for c in loc_b["components"]] == ["shared"]
        # Confirm location-scoping of attributes payload too.
        loc_a_shared = next(c for c in loc_a["components"] if c["componentId"] == "shared")
        loc_b_shared = next(c for c in loc_b["components"] if c["componentId"] == "shared")
        assert loc_a_shared["attributes"] == "loc: A\n"
        assert loc_b_shared["attributes"] == "loc: B\n"

        # Delete in locA must not affect locB.
        _delete_component(context, "shared", location_name="locA")
        loc_a_after = _list_components(context, location_name="locA").data[
            "uiComponentsForLocationOrError"
        ]
        loc_b_after = _list_components(context, location_name="locB").data[
            "uiComponentsForLocationOrError"
        ]
        assert [c["componentId"] for c in loc_a_after["components"]] == ["only_in_a"]
        assert [c["componentId"] for c in loc_b_after["components"]] == ["shared"]


def test_mutations_blocked_when_read_only():
    """Read-only viewers cannot mutate UI components."""
    with graphql_context_with_storage(read_only=True) as context:
        set_result = _set_component(context, "comp1")
        assert set_result.data["setUIComponent"]["__typename"] == "UnauthorizedError"

        delete_result = _delete_component(context, "comp1")
        assert delete_result.data["deleteUIComponent"]["__typename"] == "UnauthorizedError"

        # Listing must still work for read-only viewers.
        list_result = _list_components(context)
        assert list_result.data["uiComponentsForLocationOrError"]["__typename"] == "UIComponents"
