import os

from dagster import RepositoryDefinition, pipeline, solid
from dagster.core.definitions.container import get_container_snapshot
from dagster.core.snap.repository_snapshot import RepositorySnapshot
from dagster.serdes import serialize_dagster_namedtuple


def noop_repo():
    @solid
    def noop_solid(_):
        return 1

    @pipeline
    def noop_pipeline():
        noop_solid()

    return RepositoryDefinition(name='noop_repo', pipeline_defs=[noop_pipeline])


# pylint: disable=unused-argument
def mock_snapshot_provider(image, command, volumes):
    repo_snapshot = RepositorySnapshot.from_repository_definition(noop_repo())
    with open(
        os.path.abspath(os.path.join(list(volumes.keys())[0], 'asuperuniqueid.json')), 'w+'
    ) as fp:
        fp.write(serialize_dagster_namedtuple(repo_snapshot))


def test_container_snapshot_provider(mocker):
    mocker.patch('dagster.core.definitions.container.uuid4', return_value='asuperuniqueid')

    execute_container_mock = mocker.patch(
        'dagster.core.definitions.container.run_serialized_container_command',
        side_effect=mock_snapshot_provider,
    )
    snapshot = get_container_snapshot("foo:latest")
    execute_container_mock.assert_called_with(
        image="foo:latest",
        command='dagster repository snapshot {}'.format(
            os.path.join('/data', 'asuperuniqueid.json')
        ),
        volumes=mocker.ANY,
    )
    assert isinstance(snapshot, RepositorySnapshot)
    assert snapshot == RepositorySnapshot.from_repository_definition(noop_repo())
