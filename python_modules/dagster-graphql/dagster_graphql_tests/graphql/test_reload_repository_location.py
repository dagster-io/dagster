import sys
from unittest import mock

from dagster import file_relative_path, repository
from dagster.cli.workspace.load import location_origins_from_yaml_paths
from dagster.core.code_pointer import CodePointer
from dagster.core.host_representation import (
    ManagedGrpcPythonEnvRepositoryLocationOrigin,
    external_repository_data_from_def,
)
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.grpc.types import ListRepositoriesResponse
from dagster_graphql.test.utils import execute_dagster_graphql

from .graphql_context_test_suite import GraphQLContextVariant, make_graphql_context_test_suite

# import dagster.api.utils


class TestReloadWorkspace(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.readonly_in_memory_instance_multi_location()]
    )
):
    def test_reload_workspace(self, graphql_context):
        result = execute_dagster_graphql(graphql_context, RELOAD_WORKSPACE_QUERY)

        assert result
        assert result.data
        assert result.data["reloadWorkspace"]
        assert result.data["reloadWorkspace"]["__typename"] == "RepositoryLocationConnection"

        nodes = result.data["reloadWorkspace"]["nodes"]

        assert len(nodes) == 2

        assert all([node["__typename"] == "RepositoryLocation" for node in nodes])

        original_origins = location_origins_from_yaml_paths(
            [file_relative_path(__file__, "multi_location.yaml")]
        )

        # simulate removing all the origins
        with mock.patch(
            "dagster.cli.workspace.cli_target.location_origins_from_yaml_paths",
        ) as origins_mock:

            # simulate removing an origin, reload

            origins_mock.return_value = original_origins[0:1]
            result = execute_dagster_graphql(graphql_context, RELOAD_WORKSPACE_QUERY)

            assert result
            assert result.data
            assert result.data["reloadWorkspace"]
            assert result.data["reloadWorkspace"]["__typename"] == "RepositoryLocationConnection"

            nodes = result.data["reloadWorkspace"]["nodes"]

            assert len(nodes) == 1

            assert all([node["__typename"] == "RepositoryLocation" for node in nodes])

            # Simulate adding an origin with an error, reload

            original_origins.append(
                ManagedGrpcPythonEnvRepositoryLocationOrigin(
                    location_name="error_location",
                    loadable_target_origin=LoadableTargetOrigin(
                        python_file="made_up_file.py", executable_path=sys.executable
                    ),
                )
            )

            origins_mock.return_value = original_origins

            result = execute_dagster_graphql(graphql_context, RELOAD_WORKSPACE_QUERY)

            assert result
            assert result.data
            assert result.data["reloadWorkspace"]
            assert result.data["reloadWorkspace"]["__typename"] == "RepositoryLocationConnection"

            nodes = result.data["reloadWorkspace"]["nodes"]
            assert len(nodes) == 3

            assert len([node for node in nodes if node["__typename"] == "RepositoryLocation"]) == 2
            failures = [
                node for node in nodes if node["__typename"] == "RepositoryLocationLoadFailure"
            ]
            assert len(failures) == 1
            assert failures[0]["name"] == "error_location"

            # Add another origin without an error, reload

            original_origins.append(original_origins[0]._replace(location_name="location_copy"))
            origins_mock.return_value = original_origins

            result = execute_dagster_graphql(graphql_context, RELOAD_WORKSPACE_QUERY)

            nodes = result.data["reloadWorkspace"]["nodes"]
            assert len(nodes) == 4

            assert len([node for node in nodes if node["__typename"] == "RepositoryLocation"]) == 3
            failures = [
                node for node in nodes if node["__typename"] == "RepositoryLocationLoadFailure"
            ]
            assert len(failures) == 1

            assert "location_copy" in [node["name"] for node in nodes]
            assert original_origins[0].location_name in [node["name"] for node in nodes]

            # Finally, update one of the origins' location names

            original_origins[0] = original_origins[0]._replace(location_name="new_location_name")

            result = execute_dagster_graphql(graphql_context, RELOAD_WORKSPACE_QUERY)

            nodes = result.data["reloadWorkspace"]["nodes"]
            assert len(nodes) == 4

            assert len([node for node in nodes if node["__typename"] == "RepositoryLocation"]) == 3
            failures = [
                node for node in nodes if node["__typename"] == "RepositoryLocationLoadFailure"
            ]
            assert len(failures) == 1

            assert "new_location_name" in [node["name"] for node in nodes]


class TestReloadRepositoriesOutOfProcess(
    make_graphql_context_test_suite(
        context_variants=[GraphQLContextVariant.readonly_in_memory_instance_managed_grpc_env()]
    )
):
    def test_out_of_process_reload_location(self, graphql_context):
        result = execute_dagster_graphql(
            graphql_context, RELOAD_REPOSITORY_LOCATION_QUERY, {"repositoryLocationName": "test"}
        )

        assert result
        assert result.data
        assert result.data["reloadRepositoryLocation"]
        assert result.data["reloadRepositoryLocation"]["__typename"] == "RepositoryLocation"
        assert result.data["reloadRepositoryLocation"]["name"] == "test"
        repositories = result.data["reloadRepositoryLocation"]["repositories"]
        assert len(repositories) == 1
        assert repositories[0]["name"] == "test_repo"

        assert result.data["reloadRepositoryLocation"]["isReloadSupported"] is True

        with mock.patch(
            # note it where the function is *used* that needs to mocked, not
            # where it is defined.
            # see https://docs.python.org/3/library/unittest.mock.html#where-to-patch
            "dagster.core.host_representation.repository_location.sync_list_repositories_grpc"
        ) as cli_command_mock:

            with mock.patch(
                # note it where the function is *used* that needs to mocked, not
                # where it is defined.
                # see https://docs.python.org/3/library/unittest.mock.html#where-to-patch
                "dagster.core.host_representation.repository_location.sync_get_streaming_external_repositories_data_grpc"
            ) as external_repository_mock:

                @repository
                def new_repo():
                    return []

                new_repo_data = external_repository_data_from_def(new_repo)

                external_repository_mock.return_value = {"new_repo": new_repo_data}

                cli_command_mock.return_value = ListRepositoriesResponse(
                    repository_symbols=[],
                    executable_path=sys.executable,
                    repository_code_pointer_dict={
                        "new_repo": CodePointer.from_python_file(__file__, "new_repo", None)
                    },
                )

                result = execute_dagster_graphql(
                    graphql_context,
                    RELOAD_REPOSITORY_LOCATION_QUERY,
                    {"repositoryLocationName": "test"},
                )

                assert cli_command_mock.call_count == 1
                assert external_repository_mock.call_count == 1

                repositories = result.data["reloadRepositoryLocation"]["repositories"]
                assert len(repositories) == 1
                assert repositories[0]["name"] == "new_repo"

    def test_reload_failure(self, graphql_context):
        result = execute_dagster_graphql(
            graphql_context, RELOAD_REPOSITORY_LOCATION_QUERY, {"repositoryLocationName": "test"}
        )

        assert result
        assert result.data
        assert result.data["reloadRepositoryLocation"]
        assert result.data["reloadRepositoryLocation"]["__typename"] == "RepositoryLocation"
        assert result.data["reloadRepositoryLocation"]["name"] == "test"
        repositories = result.data["reloadRepositoryLocation"]["repositories"]
        assert len(repositories) == 1
        assert repositories[0]["name"] == "test_repo"
        assert result.data["reloadRepositoryLocation"]["isReloadSupported"] is True

        with mock.patch(
            # note it where the function is *used* that needs to mocked, not
            # where it is defined.
            # see https://docs.python.org/3/library/unittest.mock.html#where-to-patch
            "dagster.core.host_representation.repository_location.sync_list_repositories_grpc"
        ) as cli_command_mock:
            cli_command_mock.side_effect = Exception("Mocked repository load failure")

            result = execute_dagster_graphql(
                graphql_context,
                RELOAD_REPOSITORY_LOCATION_QUERY,
                {"repositoryLocationName": "test"},
            )

            assert result
            assert result.data
            assert result.data["reloadRepositoryLocation"]
            assert (
                result.data["reloadRepositoryLocation"]["__typename"]
                == "RepositoryLocationLoadFailure"
            )
            assert result.data["reloadRepositoryLocation"]["name"] == "test"
            assert (
                "Mocked repository load failure"
                in result.data["reloadRepositoryLocation"]["error"]["message"]
            )

            # Verify failure is idempotent
            result = execute_dagster_graphql(
                graphql_context,
                RELOAD_REPOSITORY_LOCATION_QUERY,
                {"repositoryLocationName": "test"},
            )

            assert result
            assert result.data
            assert result.data["reloadRepositoryLocation"]
            assert (
                result.data["reloadRepositoryLocation"]["__typename"]
                == "RepositoryLocationLoadFailure"
            )
            assert result.data["reloadRepositoryLocation"]["name"] == "test"
            assert (
                "Mocked repository load failure"
                in result.data["reloadRepositoryLocation"]["error"]["message"]
            )

        # can be reloaded again successfully
        result = execute_dagster_graphql(
            graphql_context,
            RELOAD_REPOSITORY_LOCATION_QUERY,
            {"repositoryLocationName": "test"},
        )

        assert result
        assert result.data
        assert result.data["reloadRepositoryLocation"]
        assert result.data["reloadRepositoryLocation"]["__typename"] == "RepositoryLocation"
        assert result.data["reloadRepositoryLocation"]["name"] == "test"
        repositories = result.data["reloadRepositoryLocation"]["repositories"]
        assert len(repositories) == 1
        assert repositories[0]["name"] == "test_repo"
        assert result.data["reloadRepositoryLocation"]["isReloadSupported"] is True


RELOAD_REPOSITORY_LOCATION_QUERY = """
mutation ($repositoryLocationName: String!) {
   reloadRepositoryLocation(repositoryLocationName: $repositoryLocationName) {
      __typename
      ... on RepositoryLocation {
        name
        repositories {
          name
          displayMetadata {
            key
            value
          }
        }
        isReloadSupported
      }
      ... on RepositoryLocationLoadFailure {
          name
          error {
              message
          }
      }
   }
}
"""

RELOAD_WORKSPACE_QUERY = """
mutation {
   reloadWorkspace {
      __typename
      ... on RepositoryLocationConnection {
        nodes {
          __typename
          ... on RepositoryLocation {
            id
            name
            repositories {
              name
            }
            isReloadSupported
          }
          ... on RepositoryLocationLoadFailure {
            id
            name
            error {
              message
            }
          }
        }
      }
    }
}
"""


class TestReloadRepositoriesManagedGrpc(
    make_graphql_context_test_suite(
        context_variants=[
            GraphQLContextVariant.readonly_in_memory_instance_managed_grpc_env(),
        ]
    )
):
    def test_managed_grpc_reload_location(self, graphql_context):
        result = execute_dagster_graphql(
            graphql_context, RELOAD_REPOSITORY_LOCATION_QUERY, {"repositoryLocationName": "test"}
        )

        assert result
        assert result.data
        assert result.data["reloadRepositoryLocation"]
        assert result.data["reloadRepositoryLocation"]["__typename"] == "RepositoryLocation"
        assert result.data["reloadRepositoryLocation"]["name"] == "test"

        repositories = result.data["reloadRepositoryLocation"]["repositories"]
        assert len(repositories) == 1
        assert repositories[0]["name"] == "test_repo"

        metadatas = repositories[0]["displayMetadata"]
        metadata_dict = {metadata["key"]: metadata["value"] for metadata in metadatas}

        assert (
            "python_file" in metadata_dict
            or "module_name" in metadata_dict
            or "package_name" in metadata_dict
        )

        assert result.data["reloadRepositoryLocation"]["isReloadSupported"] is True
