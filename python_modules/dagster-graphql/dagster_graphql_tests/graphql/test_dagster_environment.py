import sys

from dagster.core.host_representation import ManagedGrpcPythonEnvRepositoryLocationOrigin
from dagster.core.test_utils import instance_for_test
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster._utils import file_relative_path


def test_dagster_out_of_process_location():
    with instance_for_test() as instance:
        with ManagedGrpcPythonEnvRepositoryLocationOrigin(
            location_name="test_location",
            loadable_target_origin=LoadableTargetOrigin(
                executable_path=sys.executable,
                python_file=file_relative_path(__file__, "setup.py"),
                attribute="test_repo",
            ),
        ).create_single_location(instance) as env:
            assert env.get_repository("test_repo")
