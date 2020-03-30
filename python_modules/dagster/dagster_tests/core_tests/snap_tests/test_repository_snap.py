from dagster import RepositoryDefinition, pipeline, solid
from dagster.core.snap.pipeline_snapshot import PipelineSnapshot
from dagster.core.snap.repository_snapshot import RepositorySnapshot


def test_repository_snap_all_props():
    @solid
    def noop_solid(_):
        pass

    @pipeline
    def noop_pipeline():
        noop_solid()

    repo = RepositoryDefinition(name='noop_repo', pipeline_defs=[noop_pipeline])
    repo_snap = RepositorySnapshot.from_repository_definition(repo)

    assert repo_snap.name == 'noop_repo'
    assert len(repo_snap.pipeline_snapshots) == 1
    assert isinstance(repo_snap.pipeline_snapshots[0], PipelineSnapshot)
    assert repo_snap.pipeline_snapshots[0].name == 'noop_pipeline'
    assert repo_snap.pipeline_snapshots[0].description is None
    assert repo_snap.pipeline_snapshots[0].tags == {}


def test_repository_snap_empty():
    repo = RepositoryDefinition(name='empty_repo', pipeline_defs=[])
    repo_snap = RepositorySnapshot.from_repository_definition(repo)
    assert repo_snap.name == 'empty_repo'
    assert len(repo_snap.pipeline_snapshots) == 0
