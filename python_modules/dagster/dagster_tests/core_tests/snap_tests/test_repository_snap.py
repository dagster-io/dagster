from dagster import RepositoryDefinition, pipeline, solid
from dagster.core.snap import PipelineSnapshot, active_repository_data_from_def
from dagster.core.snap.active_data import ActivePipelineData


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
    assert len(active_repo_data.active_pipeline_datas) == 1
    assert isinstance(active_repo_data.active_pipeline_datas[0], ActivePipelineData)

    pipeline_snapshot = active_repo_data.active_pipeline_datas[0].pipeline_snapshot
    assert isinstance(pipeline_snapshot, PipelineSnapshot)
    assert pipeline_snapshot.name == 'noop_pipeline'
    assert pipeline_snapshot.description is None
    assert pipeline_snapshot.tags == {}


def test_repository_snap_empty():
    repo = RepositoryDefinition(name='empty_repo', pipeline_defs=[])
    active_repo_data = active_repository_data_from_def(repo)
    assert active_repo_data.name == 'empty_repo'
    assert len(active_repo_data.active_pipeline_datas) == 0
