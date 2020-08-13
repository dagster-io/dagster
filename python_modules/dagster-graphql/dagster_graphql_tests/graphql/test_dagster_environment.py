import sys

from dagster.core.host_representation import PythonEnvRepositoryLocation, RepositoryLocationHandle
from dagster.core.types.loadable_target_origin import LoadableTargetOrigin
from dagster.utils import file_relative_path


def test_dagster_out_of_process_location():
    env = PythonEnvRepositoryLocation(
        RepositoryLocationHandle.create_python_env_location(
            location_name='test_location',
            loadable_target_origin=LoadableTargetOrigin(
                executable_path=sys.executable,
                python_file=file_relative_path(__file__, 'setup.py'),
                attribute='test_repo',
            ),
        )
    )
    assert env.get_repository('test_repo')
