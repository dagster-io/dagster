from dagster_graphql.client.query import LAUNCH_PIPELINE_EXECUTION_MUTATION
from dagster_graphql.test.utils import (
    define_out_of_process_context,
    execute_dagster_graphql,
    infer_job_or_pipeline_selector,
)
from dagster_graphql_tests.graphql.test_assets import GET_ASSET_LOGICAL_VERSIONS

from dagster import asset
from dagster._core.definitions.asset_selection import AssetSelection
from dagster._core.definitions.decorators.repository_decorator import repository
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.test_utils import instance_for_test, wait_for_runs_to_finish
from dagster._core.workspace.context import WorkspaceRequestContext


def get_repo_v1():
    @asset
    def foo():
        return True

    @asset
    def bar(foo):  # pylint: disable=unused-argument
        return True

    all_job = define_asset_job("all_job", AssetSelection.all())

    @repository
    def repo():
        return [all_job, foo, bar]

    return repo


def get_repo_v2():
    @asset
    def bar():
        return True

    all_job = define_asset_job("all_job", AssetSelection.all())

    @repository
    def repo():
        return [all_job, bar]

    return repo


def test_dependencies_changed():
    with instance_for_test() as instance:
        with define_out_of_process_context(__file__, "get_repo_v1", instance) as context_v1:
            assert _materialize_assets(context_v1)
            wait_for_runs_to_finish(context_v1.instance)
        with define_out_of_process_context(__file__, "get_repo_v2", instance) as context_v2:
            assert _fetch_logical_versions(context_v2)


def _materialize_assets(context: WorkspaceRequestContext):
    selector = infer_job_or_pipeline_selector(context, "all_job")
    return execute_dagster_graphql(
        context,
        LAUNCH_PIPELINE_EXECUTION_MUTATION,
        variables={
            "executionParams": {
                "selector": selector,
            }
        },
    )


def _fetch_logical_versions(context: WorkspaceRequestContext):
    selector = infer_job_or_pipeline_selector(context, "all_job")
    return execute_dagster_graphql(
        context,
        GET_ASSET_LOGICAL_VERSIONS,
        variables={
            "pipelineSelector": selector,
        },
    )
