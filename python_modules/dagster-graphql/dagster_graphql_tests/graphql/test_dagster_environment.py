from dagster_graphql.implementation.context import OutOfProcessRepositoryLocation

from dagster.core.code_pointer import FileCodePointer
from dagster.utils import file_relative_path


def test_dagster_out_of_process_environment():
    env = OutOfProcessRepositoryLocation(
        'test', FileCodePointer(file_relative_path(__file__, 'setup.py'), 'define_repository'),
    )
    assert env.get_repository('test')
