import sys
import time
from typing import Any
from unittest import mock

from dagster import file_relative_path
from dagster._core.host_representation import ManagedGrpcPythonEnvCodeLocationOrigin
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._core.workspace.load import location_origins_from_yaml_paths
from dagster.version import __version__ as dagster_version
from dagster_graphql.test.utils import execute_dagster_graphql
from dagster_graphql.version import __version__ as dagster_graphql_version

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
                dagsterLibraryVersions {
                  name
                  version
                }
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

LOCATION_STATUS_QUERY = """
query {
   locationStatusesOrError {
      __typename
      ... on WorkspaceLocationStatusEntries {
        entries {
          __typename
          id
          loadStatus
          updateTimestamp
        }
      }
      ... on PythonError {
          message
          stack
      }
    }
}
"""

BaseTestSuite: Any = make_graphql_context_test_suite(
    context_variants=[GraphQLContextVariant.non_launchable_sqlite_instance_multi_location()]
)


class TestLoadWorkspace(BaseTestSuite):
    def test_load_workspace(self, graphql_context):
        # Add an error origin
        original_origins = location_origins_from_yaml_paths(
            [file_relative_path(__file__, "multi_location.yaml")]
        )
        with mock.patch(
            "dagster._core.workspace.load_target.location_origins_from_yaml_paths",
        ) as origins_mock:
            original_origins.append(
                ManagedGrpcPythonEnvCodeLocationOrigin(
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
                node["locationOrLoadError"]
                for node in nodes
                if node["locationOrLoadError"]["__typename"] == "RepositoryLocation"
            ]
            assert len(success_nodes) == 2
            assert success_nodes[0]["dagsterLibraryVersions"] == [
                {"name": "dagster", "version": dagster_version},
                {"name": "dagster-graphql", "version": dagster_graphql_version},
            ]

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

    def test_load_location_statuses(self, graphql_context):
        original_origins = location_origins_from_yaml_paths(
            [file_relative_path(__file__, "multi_location.yaml")]
        )
        with mock.patch(
            "dagster._core.workspace.load_target.location_origins_from_yaml_paths",
        ) as origins_mock:
            # Add an error origin
            original_origins.append(
                ManagedGrpcPythonEnvCodeLocationOrigin(
                    location_name="error_location",
                    loadable_target_origin=LoadableTargetOrigin(
                        python_file="made_up_file.py", executable_path=sys.executable
                    ),
                )
            )

            origins_mock.return_value = original_origins

            reload_timestamp = time.time()

            new_context = graphql_context.reload_workspace()

            result = execute_dagster_graphql(new_context, LOCATION_STATUS_QUERY)

            assert result
            assert result.data
            assert result.data["locationStatusesOrError"]
            assert (
                result.data["locationStatusesOrError"]["__typename"]
                == "WorkspaceLocationStatusEntries"
            ), str(result.data)

            nodes = result.data["locationStatusesOrError"]["entries"]

            assert len(nodes) == 3

            assert all(
                [node["__typename"] == "WorkspaceLocationStatusEntry" for node in nodes]
            ), str(nodes)

            for node in nodes:
                assert node["loadStatus"] == "LOADED"
                assert float(node["updateTimestamp"]) > reload_timestamp
