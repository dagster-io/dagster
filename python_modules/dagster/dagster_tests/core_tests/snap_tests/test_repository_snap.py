from dagster import RepositoryDefinition, pipeline, solid
from dagster.core.snap import PipelineSnapshot, active_repository_data_from_def


def test_repository_snap_all_props():
    @solid
    def noop_solid(_):
        pass

    @pipeline
    def noop_pipeline():
        noop_solid()

    repo = RepositoryDefinition(name='noop_repo', pipeline_defs=[noop_pipeline])
    active_repo_data = active_repository_data_from_def(repo)

    assert active_repo_data.name == 'noop_repo'
    assert len(active_repo_data.pipeline_snapshots) == 1
    assert isinstance(active_repo_data.pipeline_snapshots[0], PipelineSnapshot)
    assert active_repo_data.pipeline_snapshots[0].name == 'noop_pipeline'
    assert active_repo_data.pipeline_snapshots[0].description is None
    assert active_repo_data.pipeline_snapshots[0].tags == {}


def test_repository_snap_empty():
    repo = RepositoryDefinition(name='empty_repo', pipeline_defs=[])
    active_repo_data = active_repository_data_from_def(repo)
    assert active_repo_data.name == 'empty_repo'
    assert len(active_repo_data.pipeline_snapshots) == 0
