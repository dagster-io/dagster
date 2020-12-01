from dagster.core.events import EngineEventData, EventMetadataEntry
from dagster.core.instance import is_memoized_run
from dagster.core.storage.pipeline_run import PipelineRunStatus
from dagster.core.storage.tags import MEMOIZED_RUN_TAG
from dagster.core.utils import make_new_run_id
from dagster.utils import merge_dicts

from ..external import ensure_valid_config, get_external_execution_plan_or_raise
from ..resume_retry import compute_step_keys_to_execute


def create_valid_pipeline_run(graphene_info, external_pipeline, execution_params):
    ensure_valid_config(external_pipeline, execution_params.mode, execution_params.run_config)

    step_keys_to_execute = compute_step_keys_to_execute(
        graphene_info, external_pipeline, execution_params
    )

    external_execution_plan = get_external_execution_plan_or_raise(
        graphene_info=graphene_info,
        external_pipeline=external_pipeline,
        mode=execution_params.mode,
        run_config=execution_params.run_config,
        step_keys_to_execute=step_keys_to_execute,
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
