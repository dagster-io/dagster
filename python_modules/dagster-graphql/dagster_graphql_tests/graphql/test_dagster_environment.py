import sys

from dagster._core.host_representation import ManagedGrpcPythonEnvCodeLocationOrigin
from dagster._core.test_utils import instance_for_test
from dagster._core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._utils import file_relative_path


def test_dagster_out_of_process_location():
    with instance_for_test() as instance:
        with ManagedGrpcPythonEnvCodeLocationOrigin(
            location_name="test_location",
            loadable_target_origin=LoadableTargetOrigin(
                executable_path=sys.executable,
                python_file=file_relative_path(__file__, "repo.py"),
                attribute="test_repo",
            ),
        ).create_single_location(instance) as env:
            assert env.get_repository("test_repo")
