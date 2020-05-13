from dagster import RepositoryDefinition, pipeline, solid
from dagster.core.host_representation import ExternalPipelineData, external_repository_data_from_def
from dagster.core.snap import PipelineSnapshot


def test_repository_snap_all_props():
    @solid
    def noop_solid(_):
        pass

    @pipeline
    def noop_pipeline():
        noop_solid()

    repo = RepositoryDefinition(name='noop_repo', pipeline_defs=[noop_pipeline])
    external_repo_data = external_repository_data_from_def(repo)

    assert external_repo_data.name == 'noop_repo'
    assert len(external_repo_data.external_pipeline_datas) == 1
    assert isinstance(external_repo_data.external_pipeline_datas[0], ExternalPipelineData)

    pipeline_snapshot = external_repo_data.external_pipeline_datas[0].pipeline_snapshot
    assert isinstance(pipeline_snapshot, PipelineSnapshot)
    assert pipeline_snapshot.name == 'noop_pipeline'
    assert pipeline_snapshot.description is None
    assert pipeline_snapshot.tags == {}


def test_repository_snap_empty():
    repo = RepositoryDefinition(name='empty_repo', pipeline_defs=[])
    external_repo_data = external_repository_data_from_def(repo)
    assert external_repo_data.name == 'empty_repo'
    assert len(external_repo_data.external_pipeline_datas) == 0
