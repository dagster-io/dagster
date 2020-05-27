from dagster_graphql.implementation.context import OutOfProcessDagsterEnvironment

from .setup import get_repository_handle


def test_dagster_out_of_process_environment():
    env = OutOfProcessDagsterEnvironment('test', get_repository_handle())
    assert env.get_repository('test')
