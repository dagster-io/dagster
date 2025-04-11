import json
from unittest import mock

from dagster import Definitions
from dagster._core.definitions.repository_definition.repository_definition import (
    RepositoryDefinition,
)
from dagster._core.test_utils import ensure_dagster_tests_import, instance_for_test
from dagster_graphql.test.utils import define_out_of_process_context, execute_dagster_graphql
from dagster_shared.serdes.objects.package_entry import PluginObjectKey

ensure_dagster_tests_import()

GET_DOCS_JSON_QUERY = """
query GetDocsJson {
  locationDocsJsonOrError(repositorySelector: {repositoryLocationName: "test_location", repositoryName: "__repository__"}) {
    __typename
    ... on LocationDocsJson {
      json
    }
    ... on PythonError {
      message
    }
  }
}
"""


def get_empty_repo() -> RepositoryDefinition:
    return Definitions().get_repository_def()


def test_get_empty_docs_json():
    with (
        instance_for_test() as instance,
        define_out_of_process_context(__file__, "get_empty_repo", instance) as context,
    ):
        get_docs_json_result = execute_dagster_graphql(context, GET_DOCS_JSON_QUERY)
        assert (
            get_docs_json_result.data["locationDocsJsonOrError"]["__typename"] == "LocationDocsJson"
        )
        assert get_docs_json_result.data["locationDocsJsonOrError"]["json"] is not None

        json_contents = json.loads(get_docs_json_result.data["locationDocsJsonOrError"]["json"])
        assert len(json_contents) == 0


def get_components_repo() -> RepositoryDefinition:
    with mock.patch(
        "dagster.components.core.package_entry.discover_entry_point_package_objects"
    ) as mock_discover_entry_point_package_objects:
        import dagster_test.components
        from dagster.components.core.package_entry import get_package_objects_in_module

        from dagster_graphql_tests.graphql.components import defs as defs

        objects = {}
        for name, obj in get_package_objects_in_module(dagster_test.components):
            key = PluginObjectKey(name=name, namespace="dagster_test")
            objects[key] = obj

        mock_discover_entry_point_package_objects.return_value = objects

        from dagster.components.core.load_defs import load_defs

        return load_defs(defs).get_repository_def()


def test_get_docs_json():
    with (
        instance_for_test() as instance,
        define_out_of_process_context(__file__, "get_components_repo", instance) as context,
    ):
        get_docs_json_result = execute_dagster_graphql(context, GET_DOCS_JSON_QUERY)
        assert (
            get_docs_json_result.data["locationDocsJsonOrError"]["__typename"] == "LocationDocsJson"
        )
        assert get_docs_json_result.data["locationDocsJsonOrError"]["json"] is not None

        json_contents = json.loads(get_docs_json_result.data["locationDocsJsonOrError"]["json"])
        assert len(json_contents) == 1
        assert json_contents[0]["name"] == "dagster_test"
