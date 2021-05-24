import gc
import re
from contextlib import ExitStack
from unittest import mock

import pytest
from dagster import lambda_solid, pipeline, repository
from dagster.cli.workspace.context import WorkspaceProcessContext
from dagster.core.host_representation.repository_location import GrpcServerRepositoryLocation
from dagster.core.test_utils import instance_for_test
from dagster_graphql.test.utils import define_out_of_process_workspace, main_repo_location_name


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
    with instance_for_test():
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
                        define_out_of_process_workspace(__file__, "get_repo")
                    )

                assert not workspace.has_repository_location(main_repo_location_name())
                assert workspace.has_repository_location_error(main_repo_location_name())

            workspace.reload_repository_location(main_repo_location_name())
            assert workspace.has_repository_location(main_repo_location_name())


def test_reload_on_process_context():
    with instance_for_test() as instance:
        with define_out_of_process_workspace(__file__, "get_repo") as workspace:

            # Create a process context
            process_context = WorkspaceProcessContext(workspace=workspace, instance=instance)

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
        with define_out_of_process_workspace(__file__, "get_repo") as workspace:
            assert workspace.repository_locations_count == 1

            # Create a process context
            process_context = WorkspaceProcessContext(workspace=workspace, instance=instance)

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
        with define_out_of_process_workspace(__file__, "get_repo") as workspace:
            assert workspace.repository_locations_count == 1

            # Create a process context
            process_context = WorkspaceProcessContext(workspace=workspace, instance=instance)
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


def test_handle_cleaup_by_workspace_context_exit():
    with mock.patch.object(GrpcServerRepositoryLocation, "cleanup") as mock_method:
        with define_out_of_process_workspace(__file__, "get_repo") as _:
            pass

    assert mock_method.called


def test_handle_cleaup_by_gc_without_request_context():

    called = {"yup": False}

    def call_me():
        called["yup"] = True

    with instance_for_test() as instance:
        with define_out_of_process_workspace(__file__, "get_repo") as workspace:
            assert workspace.repository_locations_count == 1

            # Create a process context
            process_context = WorkspaceProcessContext(workspace=workspace, instance=instance)

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
