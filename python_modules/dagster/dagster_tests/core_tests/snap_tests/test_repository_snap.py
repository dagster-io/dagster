from dagster import job, op, repository
from dagster._core.host_representation import (
    ExternalPipelineData,
    external_repository_data_from_def,
)
from dagster._core.snap import PipelineSnapshot


def test_repository_snap_all_props():
    @op
    def noop_op(_):
        pass

    @job
    def noop_job():
        noop_op()

    @repository
    def noop_repo():
        return [noop_job]

    external_repo_data = external_repository_data_from_def(noop_repo)

    assert external_repo_data.name == "noop_repo"
    assert len(external_repo_data.external_pipeline_datas) == 1
    assert isinstance(external_repo_data.external_pipeline_datas[0], ExternalPipelineData)

    pipeline_snapshot = external_repo_data.external_pipeline_datas[0].pipeline_snapshot
    assert isinstance(pipeline_snapshot, PipelineSnapshot)
    assert pipeline_snapshot.name == "noop_job"
    assert pipeline_snapshot.description is None
    assert pipeline_snapshot.tags == {}


def test_repository_snap_empty():
    @repository
    def empty_repo():
        return []

    external_repo_data = external_repository_data_from_def(empty_repo)
    assert external_repo_data.name == "empty_repo"
    assert len(external_repo_data.external_pipeline_datas) == 0
