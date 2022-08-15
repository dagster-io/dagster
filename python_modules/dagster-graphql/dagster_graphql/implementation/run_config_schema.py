from graphene import ResolveInfo

import dagster._check as check
from dagster._config import validate_config_from_snap
from dagster._core.host_representation import RepresentedPipeline

from .external import get_external_pipeline_or_raise
from .utils import PipelineSelector, UserFacingGraphQLError, capture_error


@capture_error
def resolve_run_config_schema_or_error(graphene_info, selector, mode):
    from ..schema.errors import GrapheneModeNotFoundError
    from ..schema.run_config import GrapheneRunConfigSchema

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(selector, "selector", PipelineSelector)
    check.opt_str_param(mode, "mode")

    external_pipeline = get_external_pipeline_or_raise(graphene_info, selector)

    if mode is None:
        mode = external_pipeline.get_default_mode_name()

    if not external_pipeline.has_mode(mode):
        raise UserFacingGraphQLError(GrapheneModeNotFoundError(mode=mode, selector=selector))

    return GrapheneRunConfigSchema(
        represented_pipeline=external_pipeline,
        mode=mode,
    )


@capture_error
def resolve_is_run_config_valid(graphene_info, represented_pipeline, mode, run_config):
    from ..schema.pipelines.config import (
        GraphenePipelineConfigValidationError,
        GraphenePipelineConfigValidationValid,
        GrapheneRunConfigValidationInvalid,
    )

    check.inst_param(graphene_info, "graphene_info", ResolveInfo)
    check.inst_param(represented_pipeline, "represented_pipeline", RepresentedPipeline)
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
        raise UserFacingGraphQLError(
            GrapheneRunConfigValidationInvalid(
                pipeline_name=represented_pipeline.name,
                errors=[
                    GraphenePipelineConfigValidationError.from_dagster_error(
                        represented_pipeline.config_schema_snapshot,
                        err,
                    )
                    for err in validated_config.errors
                ],
            )
        )

    return GraphenePipelineConfigValidationValid(represented_pipeline.name)
