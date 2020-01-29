import json

from dagster_graphql.cli import execute_query_against_remote
from dagster_graphql.implementation.utils import ExecutionMetadata, ExecutionParams

from dagster import check
from dagster.core.definitions.mode import DEFAULT_MODE_NAME
from dagster.core.definitions.pipeline import ExecutionSelector

from .query import START_PIPELINE_EXECUTION_MUTATION


def execute_remote_pipeline_run(
    host, pipeline_name, environment_dict=None, tags=None, solid_subset=None, mode=None
):
    check.str_param(host, 'host')
    check.str_param(pipeline_name, 'pipeline_name')
    environment_dict = check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)
    check.opt_dict_param(tags, 'tags', key_type=str, value_type=str)
    check.opt_nullable_list_param(solid_subset, 'solid_subset', of_type=str)
    mode = check.opt_str_param(mode, 'mode', DEFAULT_MODE_NAME)

    selector = ExecutionSelector(pipeline_name, solid_subset)
    execution_params = ExecutionParams(
        selector=selector,
        environment_dict=environment_dict,
        mode=mode,
        execution_metadata=ExecutionMetadata(run_id=None, tags=tags or {}),
        step_keys=None,
        previous_run_id=None,
    )

    result = execute_query_against_remote(
        host,
        START_PIPELINE_EXECUTION_MUTATION,
        variables=json.dumps({'executionParams': execution_params.to_graphql_input()}),
    )

    return result
