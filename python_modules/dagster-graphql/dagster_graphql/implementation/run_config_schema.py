from collections.abc import Mapping
from typing import TYPE_CHECKING, Optional

import dagster._check as check
from dagster._config import validate_config_from_snap
from dagster._core.remote_representation import RepresentedJob
from dagster._core.remote_representation.external_data import DEFAULT_MODE_NAME

from dagster_graphql.implementation.external import get_remote_job_or_raise
from dagster_graphql.implementation.utils import JobSubsetSelector, UserFacingGraphQLError
from dagster_graphql.schema.errors import GrapheneModeNotFoundError
from dagster_graphql.schema.util import ResolveInfo

if TYPE_CHECKING:
    from dagster_graphql.schema.pipelines.config import GraphenePipelineConfigValidationValid
    from dagster_graphql.schema.run_config import GrapheneRunConfigSchema


def resolve_run_config_schema_or_error(
    graphene_info: ResolveInfo, selector: JobSubsetSelector, mode: Optional[str] = None
) -> "GrapheneRunConfigSchema":
    from dagster_graphql.schema.run_config import GrapheneRunConfigSchema

    check.inst_param(selector, "selector", JobSubsetSelector)

    # Mode has been eliminated from the definitions layer, so we perform a "shallow" check for
    # invalid mode. This is temporary and will be removed when the GQL API transitions to
    # job/op/graph.
    if mode and mode != DEFAULT_MODE_NAME:
        return GrapheneModeNotFoundError(selector=selector, mode=mode)

    remote_job = get_remote_job_or_raise(graphene_info, selector)

    return GrapheneRunConfigSchema(
        represented_job=remote_job,
        mode=DEFAULT_MODE_NAME,
    )


def resolve_is_run_config_valid(
    graphene_info: ResolveInfo,
    represented_pipeline: RepresentedJob,
    mode: str,
    run_config: Mapping[str, object],
) -> "GraphenePipelineConfigValidationValid":
    from dagster_graphql.schema.pipelines.config import (
        GraphenePipelineConfigValidationError,
        GraphenePipelineConfigValidationValid,
        GrapheneRunConfigValidationInvalid,
    )

    check.inst_param(represented_pipeline, "represented_pipeline", RepresentedJob)
    check.str_param(mode, "mode")
    check.dict_param(run_config, "run_config", key_type=str)

    mode_def_snap = represented_pipeline.get_mode_def_snap(mode)

    if not mode_def_snap.root_config_key:
        # historical pipeline with unknown environment type. blindly pass validation
        return GraphenePipelineConfigValidationValid(represented_pipeline.name)

    validated_config = validate_config_from_snap(
        represented_pipeline.config_schema_snapshot, mode_def_snap.root_config_key, run_config
    )

    if not validated_config.success:
        errors = check.not_none(validated_config.errors)
        raise UserFacingGraphQLError(
            GrapheneRunConfigValidationInvalid(
                pipeline_name=represented_pipeline.name,
                errors=[
                    GraphenePipelineConfigValidationError.from_dagster_error(
                        represented_pipeline.config_schema_snapshot.get_config_snap,
                        err,
                    )
                    for err in errors
                ],
            )
        )

    return GraphenePipelineConfigValidationValid(represented_pipeline.name)
