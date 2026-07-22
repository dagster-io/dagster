"""GraphQL tests for the app-managed components endpoints.

App-managed (UI-backed) components are a Dagster+-only feature. In open source the
``setAppManagedComponent`` / ``deleteAppManagedComponent`` mutations are denied for
every role (the ``EDIT_APP_MANAGED_COMPONENTS`` permission is not granted), so these
tests exercise the same operations as before but assert that the mutations are
unauthorized and never persist anything. The happy-path coverage for the mutation
logic (upsert / sorting / delete / location isolation) lives in the Cloud test
suite, where a Dagster+ context can grant the permission.
"""

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


GET_APP_MANAGED_COMPONENTS_QUERY = """
query GetAppManagedComponents($locationName: String!) {
  appManagedComponentsForLocationOrError(locationName: $locationName) {
    __typename
    ... on AppManagedComponents {
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

SET_APP_MANAGED_COMPONENT_MUTATION = """
mutation SetAppManagedComponent(
  $locationName: String!,
  $componentId: String!,
  $componentType: String!,
  $attributes: String!,
) {
  setAppManagedComponent(
    locationName: $locationName,
    componentId: $componentId,
    componentType: $componentType,
    attributes: $attributes,
  ) {
    __typename
    ... on SetAppManagedComponentSuccess {
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

DELETE_APP_MANAGED_COMPONENT_MUTATION = """
mutation DeleteAppManagedComponent($locationName: String!, $componentId: String!) {
  deleteAppManagedComponent(locationName: $locationName, componentId: $componentId) {
    __typename
    ... on DeleteAppManagedComponentSuccess {
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
        SET_APP_MANAGED_COMPONENT_MUTATION,
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
        GET_APP_MANAGED_COMPONENTS_QUERY,
        variables={"locationName": location_name},
    )


def _delete_component(
    context: WorkspaceRequestContext,
    component_id: str,
    location_name: str = LOCATION_NAME,
):
    return execute_dagster_graphql(
        context,
        DELETE_APP_MANAGED_COMPONENT_MUTATION,
        variables={"locationName": location_name, "componentId": component_id},
    )


def _assert_set_unauthorized(context: WorkspaceRequestContext, *args, **kwargs) -> None:
    result = _set_component(context, *args, **kwargs)
    assert result.data["setAppManagedComponent"]["__typename"] == "UnauthorizedError"


def _assert_delete_unauthorized(context: WorkspaceRequestContext, *args, **kwargs) -> None:
    result = _delete_component(context, *args, **kwargs)
    assert result.data["deleteAppManagedComponent"]["__typename"] == "UnauthorizedError"


def _assert_no_components(
    context: WorkspaceRequestContext, location_name: str = LOCATION_NAME
) -> None:
    payload = _list_components(context, location_name).data[
        "appManagedComponentsForLocationOrError"
    ]
    assert payload["__typename"] == "AppManagedComponents"
    assert payload["components"] == []


def test_query_empty():
    """The read path is not permission-gated and returns an empty list in OSS."""
    with graphql_context_with_storage() as context:
        result = _list_components(context)
        payload = result.data["appManagedComponentsForLocationOrError"]
        assert payload["__typename"] == "AppManagedComponents"
        assert payload["locationName"] == LOCATION_NAME
        assert payload["components"] == []


def test_set_then_query():
    """SetAppManagedComponent is denied in OSS, so nothing is persisted to query back."""
    yaml_attributes = "name: alice\nsettings:\n  enabled: true\n"
    with graphql_context_with_storage() as context:
        _assert_set_unauthorized(
            context,
            component_id="comp1",
            component_type="dagster.SomeComponent",
            attributes=yaml_attributes,
        )
        _assert_no_components(context)


def test_set_overwrites_existing_lww():
    """The set upsert (last-writer-wins) is denied in OSS; its behavior is covered by
    the Cloud suite. Here we assert repeated sets are unauthorized and persist nothing.
    """
    with graphql_context_with_storage() as context:
        _assert_set_unauthorized(context, "comp1", attributes="version: 1\n")
        _assert_set_unauthorized(
            context, "comp1", component_type="dagster.OtherComponent", attributes="version: 2\n"
        )
        _assert_no_components(context)


def test_set_multiple_components_returned_sorted():
    """Sorted listing is covered by the Cloud suite; in OSS every set is unauthorized."""
    with graphql_context_with_storage() as context:
        _assert_set_unauthorized(context, "zebra")
        _assert_set_unauthorized(context, "alpha")
        _assert_set_unauthorized(context, "mango")
        _assert_no_components(context)


def test_delete_removes_component():
    """Both set and delete are denied in OSS, so no component is ever created or removed."""
    with graphql_context_with_storage() as context:
        _assert_set_unauthorized(context, "comp1")
        _assert_set_unauthorized(context, "comp2")
        _assert_delete_unauthorized(context, "comp1")
        _assert_no_components(context)


def test_delete_is_idempotent():
    """Delete is denied in OSS; the idempotent no-op behavior is covered by the Cloud suite."""
    with graphql_context_with_storage() as context:
        _assert_delete_unauthorized(context, "never-existed")
        _assert_delete_unauthorized(context, "comp1")
        _assert_no_components(context)


def test_locations_are_isolated():
    """Location-scoping is covered by the Cloud suite; in OSS every set is unauthorized
    regardless of location, and nothing is persisted under any location.
    """
    with graphql_context_with_storage() as context:
        _assert_set_unauthorized(context, "shared", attributes="loc: A\n", location_name="locA")
        _assert_set_unauthorized(context, "shared", attributes="loc: B\n", location_name="locB")
        _assert_set_unauthorized(context, "only_in_a", attributes="loc: A\n", location_name="locA")
        _assert_no_components(context, location_name="locA")
        _assert_no_components(context, location_name="locB")


def test_mutations_blocked_when_read_only():
    """Read-only viewers cannot mutate either (they could not before this change)."""
    with graphql_context_with_storage(read_only=True) as context:
        _assert_set_unauthorized(context, "comp1")
        _assert_delete_unauthorized(context, "comp1")
        # Listing must still work for read-only viewers.
        list_result = _list_components(context)
        assert (
            list_result.data["appManagedComponentsForLocationOrError"]["__typename"]
            == "AppManagedComponents"
        )
