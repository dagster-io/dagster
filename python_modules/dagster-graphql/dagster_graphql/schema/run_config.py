from typing import Any, Optional

import dagster._check as check
import graphene
from dagster._core.host_representation import RepresentedJob
from dagster._core.host_representation.external_data import DEFAULT_MODE_NAME

from ..implementation.run_config_schema import resolve_is_run_config_valid
from .config_types import GrapheneConfigType, to_config_type
from .errors import (
    GrapheneInvalidSubsetError,
    GrapheneModeNotFoundError,
    GraphenePipelineNotFoundError,
    GraphenePythonError,
)
from .pipelines.config_result import GraphenePipelineConfigValidationResult
from .runs import GrapheneRunConfigData, parse_run_config_input
from .util import ResolveInfo, non_null_list


class GrapheneRunConfigSchema(graphene.ObjectType):
    rootConfigType = graphene.Field(
        graphene.NonNull(GrapheneConfigType),
        description="""Fetch the root environment type. Concretely this is the type that
        is in scope at the root of configuration document for a particular execution selection.
        It is the type that is in scope initially with a blank config editor.""",
    )
    allConfigTypes = graphene.Field(
        non_null_list(GrapheneConfigType),
        description="""Fetch all the named config types that are in the schema. Useful
        for things like a type browser UI, or for fetching all the types are in the
        scope of a document so that the index can be built for the autocompleting editor.
    """,
    )

    isRunConfigValid = graphene.Field(
        graphene.NonNull(GraphenePipelineConfigValidationResult),
        runConfigData=graphene.Argument(GrapheneRunConfigData),
        description="""Parse a particular run config result. The return value
        either indicates that the validation succeeded by returning
        `PipelineConfigValidationValid` or that there are configuration errors
        by returning `RunConfigValidationInvalid' which containers a list errors
        so that can be rendered for the user""",
    )

    class Meta:
        description = """The run config schema represents the all the config type
        information given a certain execution selection and mode of execution of that
        selection. All config interactions (e.g. checking config validity, fetching
        all config types, fetching in a particular config type) should be done
        through this type """
        name = "RunConfigSchema"

    def __init__(self, represented_job: RepresentedJob, mode: str):
        super().__init__()
        self._represented_job = check.inst_param(represented_job, "represented_job", RepresentedJob)
        self._mode = check.str_param(mode, "mode")

    def resolve_allConfigTypes(self, _graphene_info: ResolveInfo):
        return sorted(
            list(
                map(
                    lambda key: to_config_type(self._represented_job.config_schema_snapshot, key),
                    self._represented_job.config_schema_snapshot.all_config_keys,
                )
            ),
            key=lambda ct: ct.key,
        )

    def resolve_rootConfigType(self, _graphene_info: ResolveInfo):
        return to_config_type(
            self._represented_job.config_schema_snapshot,
            self._represented_job.get_mode_def_snap(  # type: ignore  # (possible none)
                self._mode or DEFAULT_MODE_NAME
            ).root_config_key,
        )

    def resolve_isRunConfigValid(
        self,
        graphene_info: ResolveInfo,
        runConfigData: Optional[Any] = None,  # custom scalar (GrapheneRunConfigData)
    ):
        return resolve_is_run_config_valid(
            graphene_info,
            self._represented_job,
            self._mode,
            parse_run_config_input(runConfigData or {}, raise_on_error=False),  # type: ignore
        )


class GrapheneRunConfigSchemaOrError(graphene.Union):
    class Meta:
        types = (
            GrapheneRunConfigSchema,
            GraphenePipelineNotFoundError,
            GrapheneInvalidSubsetError,
            GrapheneModeNotFoundError,
            GraphenePythonError,
        )
        name = "RunConfigSchemaOrError"
