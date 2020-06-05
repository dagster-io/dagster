from dagster.core.code_pointer import FileCodePointer
from dagster.core.host_representation import PythonEnvRepositoryLocation, RepositoryLocationHandle
from dagster.utils import file_relative_path


def test_dagster_out_of_process_location():
    env = PythonEnvRepositoryLocation(
        RepositoryLocationHandle.create_out_of_process_location(
            location_name='test_location',
            repository_code_pointer_dict={
                'test_repo': FileCodePointer(file_relative_path(__file__, 'setup.py'), 'test_repo'),
            },
        )
    )
    assert env.get_repository('test_repo')
