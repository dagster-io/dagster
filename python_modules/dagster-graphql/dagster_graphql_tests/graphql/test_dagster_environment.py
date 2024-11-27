import sys

from dagster._core.remote_representation import ManagedGrpcPythonEnvCodeLocationOrigin
from dagster._core.test_utils import instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._utils import file_relative_path
from dagster_graphql.test.utils import main_repo_location_name, main_repo_name


def test_dagster_out_of_process_location():
    with instance_for_test() as instance:
        with ManagedGrpcPythonEnvCodeLocationOrigin(
            location_name=main_repo_location_name(),
            loadable_target_origin=LoadableTargetOrigin(
                executable_path=sys.executable,
                python_file=file_relative_path(__file__, "repo.py"),
                attribute=main_repo_name(),
            ),
        ).create_single_location(instance) as env:
            assert env.get_repository(main_repo_name())
