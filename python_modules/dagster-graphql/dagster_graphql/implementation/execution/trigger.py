from __future__ import absolute_import

from graphql.execution.base import ResolveInfo

from dagster import check
from dagster.core.host_representation.external_data import (
    ExternalExecutionParamsData,
    ExternalExecutionParamsErrorData,
)
from dagster.core.host_representation.selector import PipelineSelector, TriggerSelector

from ..utils import ExecutionMetadata, ExecutionParams, capture_dauphin_error
from .run_lifecycle import create_valid_pipeline_run


@capture_dauphin_error
def trigger_execution(graphene_info, trigger_selector):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(trigger_selector, "trigger_selector", TriggerSelector)
    location = graphene_info.context.get_repository_location(trigger_selector.location_name)
    repository = location.get_repository(trigger_selector.repository_name)

    matches = [
        triggered_execution
        for triggered_execution in repository.get_external_triggered_executions()
        if triggered_execution.name == trigger_selector.trigger_name
    ]

    launched_run_ids = []
    for external_triggered_execution in matches:
        external_pipeline = repository.get_full_external_pipeline(
            external_triggered_execution.pipeline_name
        )
        result = graphene_info.context.get_external_triggered_execution_param_data(
            repository.handle, external_triggered_execution.name
        )
        if isinstance(result, ExternalExecutionParamsErrorData):
            continue

        assert isinstance(result, ExternalExecutionParamsData)

        pipeline_selector = PipelineSelector(
            location_name=location.name,
            repository_name=repository.name,
            pipeline_name=external_pipeline.name,
            solid_selection=external_triggered_execution.solid_selection,
        )
        execution_params = ExecutionParams(
            selector=pipeline_selector,
            run_config=result.run_config,
            mode=external_triggered_execution.mode,
            execution_metadata=ExecutionMetadata(run_id=None, tags=result.tags),
            step_keys=None,
        )
        pipeline_run = create_valid_pipeline_run(graphene_info, external_pipeline, execution_params)
        graphene_info.context.instance.launch_run(pipeline_run.run_id, external_pipeline)
        launched_run_ids.append(pipeline_run.run_id)

    return graphene_info.schema.type_named("TriggerExecutionSuccess")(
        launched_run_ids=launched_run_ids
    )
