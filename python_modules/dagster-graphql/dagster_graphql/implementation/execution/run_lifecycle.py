from dagster import check
from dagster.core.events import EngineEventData, EventMetadataEntry
from dagster.core.execution.plan.resume_retry import get_retry_steps_from_execution_plan
from dagster.core.execution.plan.state import KnownExecutionState
from dagster.core.host_representation import ExternalPipeline
from dagster.core.instance import is_memoized_run
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.tags import MEMOIZED_RUN_TAG, RESUME_RETRY_TAG
from dagster.core.utils import make_new_run_id
from dagster.utils import merge_dicts
from graphql.execution.base import ResolveInfo

from ..external import ensure_valid_config, get_external_execution_plan_or_raise
from ..utils import ExecutionParams


def compute_step_keys_to_execute(graphene_info, external_pipeline, execution_params):
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
    check.inst_param(execution_params, "execution_params", ExecutionParams)

    instance = graphene_info.context.instance

    if not execution_params.step_keys and is_resume_retry(execution_params):
        # Get step keys from parent_run_id if it's a resume/retry
        external_execution_plan = get_external_execution_plan_or_raise(
            graphene_info=graphene_info,
            external_pipeline=external_pipeline,
            mode=execution_params.mode,
            run_config=execution_params.run_config,
            step_keys_to_execute=None,
            known_state=None,
        )
        return get_retry_steps_from_execution_plan(
            instance, external_execution_plan, execution_params.execution_metadata.parent_run_id
        )
    else:
        known_state = None
        if execution_params.execution_metadata.parent_run_id and execution_params.step_keys:
            known_state = KnownExecutionState.for_reexecution(
                instance.all_logs(execution_params.execution_metadata.parent_run_id),
                execution_params.step_keys,
            )

        return execution_params.step_keys, known_state


def is_resume_retry(execution_params):
    check.inst_param(execution_params, "execution_params", ExecutionParams)
    return execution_params.execution_metadata.tags.get(RESUME_RETRY_TAG) == "true"


def create_valid_pipeline_run(graphene_info, external_pipeline, execution_params):
    ensure_valid_config(external_pipeline, execution_params.mode, execution_params.run_config)

    step_keys_to_execute, known_state = compute_step_keys_to_execute(
        graphene_info, external_pipeline, execution_params
    )

    external_execution_plan = get_external_execution_plan_or_raise(
        graphene_info=graphene_info,
        external_pipeline=external_pipeline,
        mode=execution_params.mode,
        run_config=execution_params.run_config,
        step_keys_to_execute=step_keys_to_execute,
        known_state=known_state,
    )
    tags = merge_dicts(external_pipeline.tags, execution_params.execution_metadata.tags)

    pipeline_run = graphene_info.context.instance.create_run(
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        execution_plan_snapshot=external_execution_plan.execution_plan_snapshot,
        parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
        pipeline_name=execution_params.selector.pipeline_name,
        run_id=execution_params.execution_metadata.run_id
        if execution_params.execution_metadata.run_id
        else make_new_run_id(),
        solids_to_execute=frozenset(execution_params.selector.solid_selection)
        if execution_params.selector.solid_selection
        else None,
        run_config=execution_params.run_config,
        mode=execution_params.mode,
        step_keys_to_execute=step_keys_to_execute,
        tags=tags,
        root_run_id=execution_params.execution_metadata.root_run_id,
        parent_run_id=execution_params.execution_metadata.parent_run_id,
        status=PipelineRunStatus.NOT_STARTED,
        external_pipeline_origin=external_pipeline.get_external_origin(),
    )

    # TODO: support memoized execution from dagit. https://github.com/dagster-io/dagster/issues/3322
    if is_memoized_run(tags):
        graphene_info.context.instance.report_engine_event(
            'Tag "{tag}" was found when initializing pipeline run, however, memoized '
            "execution is only supported from the dagster CLI. This pipeline will run, but "
            "outputs from previous executions will be ignored. "
            "In order to execute this pipeline using memoization, provide the "
            '"{tag}" tag to the `dagster pipeline execute` CLI. The CLI is documented at '
            "the provided link.".format(tag=MEMOIZED_RUN_TAG),
            pipeline_run,
            EngineEventData(
                [
                    EventMetadataEntry.url(
                        "https://docs.dagster.io/_apidocs/cli#dagster-pipeline-execute",
                        label="dagster_pipeline_execute_docs_url",
                        description="In order to execute this pipeline using memoization, provide the "
                        '"{tag}" tag to the `dagster pipeline execute` CLI. The CLI is documented at '
                        "the provided link.".format(tag=MEMOIZED_RUN_TAG),
                    )
                ]
            ),
        )

    return pipeline_run
