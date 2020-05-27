from dagster.serdes import serialize_pp
from dagster.utils.hosted_user_process import external_repo_from_repository_handle

from .setup import get_repository_handle


def test_all_snapshot_ids(snapshot):
    # This ensures that pipeline snapshots remain stable
    # If you 1) change any pipelines in dagster_graphql_test or 2) change the
    # schema of PipelineSnapshots you are free to rerecord
    repo = external_repo_from_repository_handle(get_repository_handle())
    for pipeline in sorted(repo.get_all_external_pipelines(), key=lambda p: p.name):
        snapshot.assert_match(serialize_pp(pipeline.pipeline_snapshot))
        snapshot.assert_match(pipeline.computed_pipeline_snapshot_id)
