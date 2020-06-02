from dagster.core.code_pointer import FileCodePointer
from dagster.core.host_representation import OutOfProcessRepositoryLocation
from dagster.utils import file_relative_path


def test_dagster_out_of_process_location():
    env = OutOfProcessRepositoryLocation(
        'test', FileCodePointer(file_relative_path(__file__, 'setup.py'), 'test_repo'),
    )
    assert env.get_repository('test_repo')
