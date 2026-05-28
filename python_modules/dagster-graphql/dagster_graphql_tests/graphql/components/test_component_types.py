"""Tests for the componentTypesForLocationOrError query."""

from unittest import mock

from dagster import Definitions
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.test_utils import ensure_dagster_tests_import, instance_for_test
from dagster_graphql.test.utils import define_out_of_process_context, execute_dagster_graphql
from dagster_shared.serdes.objects.package_entry import EnvRegistryKey

ensure_dagster_tests_import()

LOCATION_NAME = "test_location"


COMPONENT_TYPES_QUERY = """
query GetComponentTypes($locationName: String!) {
  componentTypesForLocationOrError(locationName: $locationName) {
    __typename
    ... on ComponentTypes {
      locationName
      componentTypes {
        name
        namespace
        example
        schema
        description
        owners
        tags
        isUiEditable
      }
    }
    ... on RepositoryLocationNotFound {
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


def get_components_repo() -> RepositoryDefinition:
    """Loads a repository with the dagster_test built-in components installed,
    populating the ``PLUGIN_COMPONENT_TYPES_JSON_METADATA_KEY`` metadata.
    """
    with mock.patch(
        "dagster.components.core.package_entry.discover_entry_point_package_objects"
    ) as mock_discover_entry_point_package_objects:
        import dagster_test.components
        from dagster.components.core.package_entry import get_package_objects_in_module

        from dagster_graphql_tests.graphql.components import defs as defs

        objects = {}
        for name, obj in get_package_objects_in_module(dagster_test.components):
            key = EnvRegistryKey(name=name, namespace="dagster_test")
            objects[key] = obj

        mock_discover_entry_point_package_objects.return_value = objects

        from dagster.components.core.load_defs import load_defs

        return load_defs(defs).get_repository_def()


def test_empty_repo_returns_no_component_types():
    with (
        instance_for_test() as instance,
        define_out_of_process_context(__file__, "get_empty_repo", instance) as context,
    ):
        result = execute_dagster_graphql(
            context, COMPONENT_TYPES_QUERY, variables={"locationName": LOCATION_NAME}
        )
        payload = result.data["componentTypesForLocationOrError"]
        assert payload["__typename"] == "ComponentTypes"
        assert payload["locationName"] == LOCATION_NAME
        assert payload["componentTypes"] == []


def test_returns_component_types_with_schemas():
    with (
        instance_for_test() as instance,
        define_out_of_process_context(__file__, "get_components_repo", instance) as context,
    ):
        result = execute_dagster_graphql(
            context, COMPONENT_TYPES_QUERY, variables={"locationName": LOCATION_NAME}
        )
        payload = result.data["componentTypesForLocationOrError"]
        assert payload["__typename"] == "ComponentTypes"
        assert payload["locationName"] == LOCATION_NAME

        component_types = payload["componentTypes"]
        # The mock installs every class exported from dagster_test.components.
        names = {c["name"] for c in component_types}
        assert "dagster_test.SimpleAssetComponent" in names
        assert "dagster_test.ComplexAssetComponent" in names

        # Returned in deterministic (sorted) order.
        assert [c["name"] for c in component_types] == sorted(names)

        # Each component should have a parsed JSON schema (i.e. a dict, not a string).
        simple = next(
            c for c in component_types if c["name"] == "dagster_test.SimpleAssetComponent"
        )
        schema = simple["schema"]
        assert isinstance(schema, dict)
        # The asset_key + value fields are declared on SimpleAssetComponent.
        properties = schema.get("properties") or {}
        assert "asset_key" in properties
        assert "value" in properties

        # Owners/tags from the component spec round-trip through.
        assert simple["owners"] == ["john@dagster.io", "jane@dagster.io"]
        assert simple["tags"] == ["a", "b", "c"]
        assert simple["description"]  # present
        # SimpleAssetComponent.get_form_config() returns ComponentFormConfig(editable=True),
        # so its schema carries x-ui-editable: true and the field surfaces here.
        assert simple["isUiEditable"] is True
        # Namespace + example come from the same metadata blob the docs
        # tab used to read directly.
        assert simple["namespace"] == "dagster_test"
        assert simple["example"]
        assert "dagster_test.SimpleAssetComponent" in simple["example"]


def test_unknown_location_returns_not_found_error():
    with (
        instance_for_test() as instance,
        define_out_of_process_context(__file__, "get_empty_repo", instance) as context,
    ):
        result = execute_dagster_graphql(
            context,
            COMPONENT_TYPES_QUERY,
            variables={"locationName": "definitely_not_a_location"},
        )
        payload = result.data["componentTypesForLocationOrError"]
        assert payload["__typename"] == "RepositoryLocationNotFound"
        assert "definitely_not_a_location" in payload["message"]
