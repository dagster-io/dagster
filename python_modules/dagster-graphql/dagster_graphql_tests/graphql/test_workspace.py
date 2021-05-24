import sys
import time
from unittest import mock

from dagster import file_relative_path
from dagster.cli.workspace.load import location_origins_from_yaml_paths
from dagster.core.host_representation import ManagedGrpcPythonEnvRepositoryLocationOrigin
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster_graphql.test.utils import execute_dagster_graphql

from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite

WORKSPACE_QUERY = """
query {
   workspaceOrError {
      __typename
      ... on Workspace {
        locationEntries {
          __typename
          id
          name
          locationOrLoadError {
            __typename
            ... on RepositoryLocation {
                id
                name
                repositories {
                    name
                }
                isReloadSupported
            }
            ... on PythonError {
              message
            }
          }
          loadStatus
          displayMetadata {
            key
            value
          }
          updatedTimestamp
        }
      }
      ... on PythonError {
          message
          stack
      }
    }
}
"""


class TestLoadWorkspace(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.non_launchable_in_memory_instance_multi_location()]
    )
):
    def test_load_workspace(self, graphql_context):
        # Add an error origin
        original_origins = location_origins_from_yaml_paths(
            [file_relative_path(__file__, "multi_location.yaml")]
        )
        with mock.patch(
            "dagster.cli.workspace.cli_target.location_origins_from_yaml_paths",
        ) as origins_mock:
            original_origins.append(
                ManagedGrpcPythonEnvRepositoryLocationOrigin(
                    location_name="error_location",
                    loadable_target_origin=LoadableTargetOrigin(
                        python_file="made_up_file.py", executable_path=sys.executable
                    ),
                )
            )

            origins_mock.return_value = original_origins

            reload_time = time.time()

            new_context = graphql_context.reload_workspace()

            result = execute_dagster_graphql(new_context, WORKSPACE_QUERY)

            assert result
            assert result.data
            assert result.data["workspaceOrError"]
            assert result.data["workspaceOrError"]["__typename"] == "Workspace", str(result.data)

            nodes = result.data["workspaceOrError"]["locationEntries"]

            assert len(nodes) == 3

            assert all([node["__typename"] == "WorkspaceLocationEntry" for node in nodes]), str(
                nodes
            )

            success_nodes = [
                node
                for node in nodes
                if node["locationOrLoadError"]["__typename"] == "RepositoryLocation"
            ]
            assert len(success_nodes) == 2

            failures = [
                node for node in nodes if node["locationOrLoadError"]["__typename"] == "PythonError"
            ]
            assert len(failures) == 1
            failure_node = failures[0]

            assert failure_node["name"] == "error_location"
            assert failure_node["loadStatus"] == "LOADED"
            assert "No such file or directory" in failure_node["locationOrLoadError"]["message"]

            for node in nodes:
                assert node["loadStatus"] == "LOADED"
                update_time = node["updatedTimestamp"]
                assert update_time >= reload_time and update_time <= time.time()

                metadatas = node["displayMetadata"]
                metadata_dict = {metadata["key"]: metadata["value"] for metadata in metadatas}

                assert (
                    "python_file" in metadata_dict
                    or "module_name" in metadata_dict
                    or "package_name" in metadata_dict
                )
