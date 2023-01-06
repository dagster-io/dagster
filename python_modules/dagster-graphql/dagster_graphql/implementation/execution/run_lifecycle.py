from typing import TYPE_CHECKING, Optional, Sequence, cast

import dagster._check as check
from dagster._core.errors import DagsterRunNotFoundError
from dagster._core.execution.plan.resume_retry import get_retry_steps_from_parent_run
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.host_representation.external import ExternalPipeline
from dagster._core.instance import DagsterInstance
from dagster._core.instance.persist_run_for_production import (
    ReexecutionInfoForProduction,
    persist_run_for_production,
)
from dagster._core.storage.pipeline_run import DagsterRun, DagsterRunStatus
from dagster._core.storage.tags import RESUME_RETRY_TAG
from graphene import ResolveInfo

from ..external import ensure_valid_config
from ..utils import ExecutionParams, UserFacingGraphQLError

if TYPE_CHECKING:
    from dagster_graphql.schema.util import HasContext


def _get_run(instance: DagsterInstance, run_id: str) -> DagsterRun:
    run = instance.get_run_by_id(run_id)
    if not run:
        raise DagsterRunNotFoundError(invalid_run_id=run_id)
    return cast(DagsterRun, run)


# consolidate this logic with logic in create_reexecuted_run
def compute_reexecution_info(
    graphene_info: "HasContext", execution_params: ExecutionParams
) -> Optional[ReexecutionInfoForProduction]:
    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(execution_params, "execution_params", ExecutionParams)

    instance = graphene_info.context.instance

    if not execution_params.execution_metadata.parent_run_id:
        check.invariant(
            not execution_params.execution_metadata.root_run_id, "parent and root are set together"
        )
        return None

    root_run_id = check.not_none(execution_params.execution_metadata.root_run_id)
    parent_run_id = check.not_none(execution_params.execution_metadata.parent_run_id)

    step_keys_to_return: Optional[Sequence[str]] = None
    known_state: Optional[KnownExecutionState] = None

    if not execution_params.step_keys and is_resume_retry(execution_params):
        # Get step keys from parent_run_id if it's a resume/retry
        parent_run = _get_run(instance, parent_run_id)
        step_keys_to_return, known_state = get_retry_steps_from_parent_run(
            instance,
            parent_run,
        )
    elif execution_params.step_keys:
        step_keys_to_return = execution_params.step_keys
        parent_run = _get_run(instance, parent_run_id)
        known_state = KnownExecutionState.build_for_reexecution(
            instance,
            parent_run,
        ).update_for_step_selection(execution_params.step_keys)

    return ReexecutionInfoForProduction(
        parent_run_id=parent_run_id,
        root_run_id=root_run_id,
        known_state=known_state,
        step_keys_to_execute=step_keys_to_return,
    )


def is_resume_retry(execution_params):
    check.inst_param(execution_params, "execution_params", ExecutionParams)
    return execution_params.execution_metadata.tags.get(RESUME_RETRY_TAG) == "true"


def create_valid_pipeline_run(
    graphene_info: "HasContext",
    external_pipeline: ExternalPipeline,
    execution_params: ExecutionParams,
):
    from ...schema.errors import GrapheneNoModeProvidedError

    mode: Optional[str]
    if execution_params.mode is None and len(external_pipeline.available_modes) > 1:
        raise UserFacingGraphQLError(
            GrapheneNoModeProvidedError(external_pipeline.name, external_pipeline.available_modes)
        )

    elif execution_params.mode is None and len(external_pipeline.available_modes) == 1:
        mode = external_pipeline.available_modes[0]

    else:
        mode = execution_params.mode

    ensure_valid_config(external_pipeline, mode, execution_params.run_config)

    reexecution_info = compute_reexecution_info(graphene_info, execution_params)

    return persist_run_for_production(
        instance=graphene_info.context.instance,
        repository_location=graphene_info.context.get_repository_location(
            execution_params.selector.location_name
        ),
        pipeline_selector=execution_params.selector,
        explicit_mode=execution_params.mode,
        run_config=execution_params.run_config,
        reexecution_info=reexecution_info,
        context_specific_tags=execution_params.execution_metadata.tags,
        explicit_run_id=execution_params.execution_metadata.run_id,
        run_status=DagsterRunStatus.NOT_STARTED,
    )
