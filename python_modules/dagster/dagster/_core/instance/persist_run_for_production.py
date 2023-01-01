from typing import Mapping, NamedTuple, Optional, Sequence

from dagster._core.definitions.utils import validate_tags
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.host_representation.repository_location import RepositoryLocation
from dagster._core.host_representation.selector import PipelineSelector
from dagster._core.instance import DagsterInstance
from dagster._core.storage.pipeline_run import DagsterRun, DagsterRunStatus
from dagster._core.utils import make_new_run_id
from dagster._utils.merger import merge_dicts


class ReexecutionInfoForProduction(NamedTuple):
    parent_run_id: str
    root_run_id: str
    known_state: Optional[KnownExecutionState]
    step_keys_to_execute: Optional[Sequence[str]]


def persist_run_for_production(
    *,
    instance: DagsterInstance,
    repository_location: RepositoryLocation,
    pipeline_selector: PipelineSelector,
    run_config: Mapping[str, object],
    context_specific_tags: Mapping[str, str],
    # TODO consider optional below here
    reexecution_info: Optional[ReexecutionInfoForProduction],
    run_status: Optional[DagsterRunStatus],
    explicit_mode: Optional[str],
    explicit_run_id: Optional[str],
) -> DagsterRun:
    external_pipeline = repository_location.get_external_pipeline(pipeline_selector)
    mode = explicit_mode or external_pipeline.get_default_mode_name()

    external_execution_plan = repository_location.get_external_execution_plan(
        external_pipeline=external_pipeline,
        run_config=run_config,
        mode=mode,
        step_keys_to_execute=reexecution_info.step_keys_to_execute if reexecution_info else None,
        known_state=reexecution_info.known_state if reexecution_info else None,
        instance=instance,
    )

    run_tags = merge_dicts(
        # validate_tags happened in scheduler creation paths but not graphql
        validate_tags(external_pipeline.tags, allow_reserved_tags=False) or {},
        context_specific_tags,
    )

    return instance.create_run(
        pipeline_snapshot=external_pipeline.pipeline_snapshot,
        parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
        execution_plan_snapshot=external_execution_plan.execution_plan_snapshot,
        pipeline_name=external_pipeline.name,
        run_id=explicit_run_id or make_new_run_id(),
        asset_selection=frozenset(pipeline_selector.asset_selection)
        if pipeline_selector.asset_selection
        else None,
        solid_selection=pipeline_selector.solid_selection,
        # solids_to_execute looks problematic
        solids_to_execute=external_pipeline.solids_to_execute,
        # solids_to_execute=frozenset(pipeline_selector.solid_selection)
        # if pipeline_selector.solid_selection
        # else None,
        run_config=run_config,
        mode=mode,
        step_keys_to_execute=external_execution_plan.step_keys_in_plan,
        tags=run_tags,
        root_run_id=reexecution_info.root_run_id if reexecution_info else None,
        parent_run_id=reexecution_info.parent_run_id if reexecution_info else None,
        status=run_status,
        external_pipeline_origin=external_pipeline.get_external_origin(),
        pipeline_code_origin=external_pipeline.get_python_origin(),
    )
