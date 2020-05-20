from dagster.core.host_representation import EnvironmentHandle, ExternalRepository
from dagster.serdes import serialize_pp

from .setup import define_repository


def test_all_snapshot_ids(snapshot):
    # This ensures that pipeline snapshots remain stable
    # If you 1) change any pipelines in dagster_graphql_test or 2) change the
    # schema of PipelineSnapshots you are free to rerecord
    repo = ExternalRepository.from_repository_def(
        define_repository(), EnvironmentHandle('<<ad_hoc>>')
    )
    for pipeline in sorted(repo.get_all_external_pipelines(), key=lambda p: p.name):
        snapshot.assert_match(serialize_pp(pipeline.pipeline_snapshot))
        snapshot.assert_match(pipeline.computed_pipeline_snapshot_id)
