from typing import Mapping, Optional

from dagster._core.definitions.utils import validate_tags
from dagster._core.host_representation.repository_location import RepositoryLocation
from dagster._core.host_representation.selector import PipelineSelector
from dagster._core.instance import DagsterInstance
from dagster._core.storage.pipeline_run import DagsterRun, DagsterRunStatus
from dagster._core.utils import make_new_run_id


def persist_run_for_production(
    *,
    instance: DagsterInstance,
    repository_location: RepositoryLocation,
    pipeline_selector: PipelineSelector,
    run_config: Mapping[str, object],
    context_specific_tags: Mapping[str, str],
    explicit_mode: Optional[str],
) -> DagsterRun:
    """
    Creates a run suitable for production using host process (i.e. External*) APIs.
    This orchestrates necessary interactions with the user process (such as
    fetching the external pipeline appropriate to the passed subset and
    compiling the execution plan). This persists a run in instance with the
    NOT_STARTED state.

    Parameters:
        instance (DagsterInstance): Instace to execute against
        repository_location (RepositoryLocation): RepositoryLocation corresponding to user code
        pipeline_selector (PipelineSelector): Selector that encapsulates subset of pipeline that will be executed
        run_config (Mapping[str, object]): Run configuration for this run
        context_specific_tags (Mapping[str, str]): Callsites typically have tags
            specific to their context (e.g. users can specify ad hoc tags for runs.
            This set of tags will be merged with the tags on the pipeline itself)
        explicit_mode Optional[str]: Explicitly override the default mode for the pipeline.
    """
    external_pipeline = repository_location.get_external_pipeline(pipeline_selector)
    mode = explicit_mode or external_pipeline.get_default_mode_name()

    external_execution_plan = repository_location.get_external_execution_plan(
        external_pipeline=external_pipeline,
        run_config=run_config,
        mode=mode,
        step_keys_to_execute=None,
        known_state=None,
        instance=instance,
    )

    run_tags = {**validate_tags(external_pipeline.tags), **validate_tags(context_specific_tags)}

    return instance.create_run(
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
        execution_plan_snapshot=external_execution_plan.execution_plan_snapshot,
        pipeline_name=external_pipeline.name,
        run_id=make_new_run_id(),
        asset_selection=frozenset(pipeline_selector.asset_selection)
        if pipeline_selector.asset_selection
        else None,
        solid_selection=pipeline_selector.solid_selection,
        solids_to_execute=external_pipeline.solids_to_execute,
        run_config=run_config,
        mode=mode,
        step_keys_to_execute=external_execution_plan.step_keys_in_plan,
        tags=run_tags,
        root_run_id=None,
        parent_run_id=None,
        status=DagsterRunStatus.NOT_STARTED,
        external_pipeline_origin=external_pipeline.get_external_origin(),
        pipeline_code_origin=external_pipeline.get_python_origin(),
    )
