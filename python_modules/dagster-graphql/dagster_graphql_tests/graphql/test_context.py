import gc
import re
from contextlib import ExitStack
from unittest import mock

import pytest
from dagster_graphql.test.utils import define_out_of_process_workspace, main_repo_location_name

from dagster import AssetKey, file_relative_path, lambda_solid, pipeline, repository
from dagster.core.host_representation.repository_location import GrpcServerRepositoryLocation
from dagster.core.test_utils import instance_for_test
from dagster.core.workspace.context import WorkspaceProcessContext
from dagster.core.workspace.load_target import PythonFileTarget


def get_repo():
    """
    This is a repo that changes name very time it's loaded
    """

    @lambda_solid
    def solid_A():
        pass

    @pipeline
    def pipe():
        solid_A()

    import random
    import string

    @repository(name="".join(random.choice(string.ascii_lowercase) for i in range(10)))
    def my_repo():
        return [pipe]

    return my_repo


def test_can_reload_on_external_repository_error():
    with instance_for_test() as instance:
        with ExitStack() as exit_stack:
            with mock.patch(
                # note it where the function is *used* that needs to mocked, not
                # where it is defined.
                # see https://docs.python.org/3/library/unittest.mock.html#where-to-patch
                "dagster.core.host_representation.repository_location.sync_get_streaming_external_repositories_data_grpc"
            ) as external_repository_mock:
                external_repository_mock.side_effect = Exception("get_external_repo_failure")

                with pytest.warns(UserWarning, match=re.escape("get_external_repo_failure")):
                    workspace = exit_stack.enter_context(
                        define_out_of_process_workspace(__file__, "get_repo", instance)
                    )

                assert not workspace.has_repository_location(main_repo_location_name())
                assert workspace.has_repository_location_error(main_repo_location_name())

            workspace.reload_repository_location(main_repo_location_name())
            assert workspace.has_repository_location(main_repo_location_name())


def test_reload_on_process_context():
    with instance_for_test() as instance:
        with define_out_of_process_workspace(__file__, "get_repo", instance) as process_context:
            request_context = process_context.create_request_context()

            # Save the repository name
            repository_location = request_context.repository_locations[0]
            repo = list(repository_location.get_repositories().values())[0]
            repo_name = repo.name

            # Reload the location and save the new repository name
            process_context.reload_repository_location(repository_location.name)

            new_request_context = process_context.create_request_context()

            repository_location = new_request_context.repository_locations[0]
            repo = list(repository_location.get_repositories().values())[0]
            new_repo_name = repo.name

            # Check that the repository has changed
            assert repo_name != new_repo_name


def test_reload_on_request_context():
    with instance_for_test() as instance:
        with define_out_of_process_workspace(__file__, "get_repo", instance) as process_context:
            assert process_context.repository_locations_count == 1

            # Create a request context from the process context
            request_context = process_context.create_request_context()

            # Save the repository name
            repository_location = request_context.repository_locations[0]
            repo = list(repository_location.get_repositories().values())[0]
            repo_name = repo.name

            # Reload the location and save the new repository name
            process_context.reload_repository_location(repository_location.name)

            new_request_context = process_context.create_request_context()
            repository_location = new_request_context.repository_locations[0]
            repo = list(repository_location.get_repositories().values())[0]
            new_repo_name = repo.name

            # Check that the repository has changed
            assert repo_name != new_repo_name

            # Check that the repository name is still the same on the old request context,
            # confirming that the old repository location is still running
            repository_location = request_context.repository_locations[0]
            repo = list(repository_location.get_repositories().values())[0]
            assert repo_name == repo.name


def test_reload_on_request_context_2():
    # This is the similar to the test `test_reload_on_request_context`,
    # but calls reload from the request_context instead of on the process_context

    with instance_for_test() as instance:
        with define_out_of_process_workspace(__file__, "get_repo", instance) as process_context:
            assert process_context.repository_locations_count == 1

            request_context = process_context.create_request_context()

            # Save the repository name
            repository_location = request_context.repository_locations[0]
            repo = list(repository_location.get_repositories().values())[0]
            repo_name = repo.name

            # Reload the location from the request context
            new_request_context = request_context.reload_repository_location(
                repository_location.name
            )

            repository_location = new_request_context.repository_locations[0]
            repo = list(repository_location.get_repositories().values())[0]
            new_repo_name = repo.name

            # Check that the repository has changed
            assert repo_name != new_repo_name

            # Check that the repository name is still the same on the old request context,
            # confirming that the old repository location is still running
            repository_location = request_context.repository_locations[0]
            repo = list(repository_location.get_repositories().values())[0]
            assert repo_name == repo.name


def test_handle_cleanup_by_workspace_context_exit():
    with instance_for_test() as instance:
        with mock.patch.object(GrpcServerRepositoryLocation, "cleanup") as mock_method:
            with define_out_of_process_workspace(__file__, "get_repo", instance):
                pass

    assert mock_method.called


def test_handle_cleaup_by_gc_without_request_context():

    called = {"yup": False}

    def call_me():
        called["yup"] = True

    with instance_for_test() as instance:
        with define_out_of_process_workspace(__file__, "get_repo", instance) as process_context:
            assert process_context.repository_locations_count == 1

            request_context = process_context.create_request_context()
            request_context.repository_locations[0].cleanup = call_me

            # Reload the location from the request context
            assert not called["yup"]
            process_context.reload_repository_location("test_location")
            assert not called["yup"]

            request_context = None

            # There are no more references to the location, so it should be GC'd
            gc.collect()
            assert called["yup"]


def test_cross_repo_asset_deps():
    with instance_for_test() as instance:
        with WorkspaceProcessContext(
            instance,
            PythonFileTarget(
                python_file=file_relative_path(__file__, "multiple_repos.py"),
                attribute=None,
                working_directory=None,
                location_name=None,
            ),
        ) as workspace_process_context:
            request_context = workspace_process_context.create_request_context()
            repo_location = request_context.repository_locations[0]

            upstream_repo = repo_location.get_repository("upstream_repo")
            downstream_repo = repo_location.get_repository("downstream_repo")

            source_asset = upstream_repo.get_external_asset_node(AssetKey("my_source_asset"))
            downstream_asset_keys = [
                dependent_asset.downstream_asset_key for dependent_asset in source_asset.depended_by
            ]
            assert len(downstream_asset_keys) == 2
            assert AssetKey("downstream_asset") in downstream_asset_keys
            assert AssetKey("second_asset") in downstream_asset_keys

            downstream_asset = downstream_repo.get_external_asset_node(AssetKey("downstream_asset"))
            downstream_asset_dependency_keys = [
                asset.upstream_asset_key for asset in downstream_asset.dependencies
            ]
            assert len(downstream_asset_dependency_keys) == 1
            assert AssetKey("my_source_asset") in downstream_asset_dependency_keys
