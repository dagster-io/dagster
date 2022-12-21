from collections import namedtuple

import dagster._check as check
import graphene
from dagster._config import (
    ConfigSchemaSnapshot,
    EvaluationError as DagsterEvaluationError,
    EvaluationStackListItemEntry,
    EvaluationStackMapKeyEntry,
    EvaluationStackMapValueEntry,
    EvaluationStackPathEntry,
    FieldNotDefinedErrorData,
    FieldsNotDefinedErrorData,
    MissingFieldErrorData,
    MissingFieldsErrorData,
    RuntimeMismatchErrorData,
    SelectorTypeErrorData,
)
from dagster._core.host_representation.represented import RepresentedPipeline
from dagster._utils.error import SerializableErrorInfo
from graphene.types.generic import GenericScalar

from ..config_types import GrapheneConfigTypeField
from ..util import non_null_list


class GrapheneEvaluationStackListItemEntry(graphene.ObjectType):
    list_index = graphene.NonNull(graphene.Int)

    class Meta:
        name = "EvaluationStackListItemEntry"

    def __init__(self, list_index):
        super().__init__()
        self._list_index = list_index

    def resolve_list_index(self, _info):
        return self._list_index


class GrapheneEvaluationStackMapKeyEntry(graphene.ObjectType):
    map_key = graphene.NonNull(GenericScalar)

    class Meta:
        name = "EvaluationStackMapKeyEntry"

    def __init__(self, map_key):
        super().__init__()
        self._map_key = map_key

    def resolve_map_key(self, _info):
        return self._map_key


class GrapheneEvaluationStackMapValueEntry(graphene.ObjectType):
    map_key = graphene.NonNull(GenericScalar)

    class Meta:
        name = "EvaluationStackMapValueEntry"

    def __init__(self, map_key):
        super().__init__()
        self._map_key = map_key

    def resolve_map_key(self, _info):
        return self._map_key


class GrapheneEvaluationStackPathEntry(graphene.ObjectType):
    field_name = graphene.NonNull(graphene.String)

    class Meta:
        name = "EvaluationStackPathEntry"

    def __init__(self, field_name):
        self._field_name = check.str_param(field_name, "field_name")
        super().__init__()

    def resolve_field_name(self, _info):
        return self._field_name


class GrapheneEvaluationStackEntry(graphene.Union):
    class Meta:
        types = (
            GrapheneEvaluationStackListItemEntry,
            GrapheneEvaluationStackPathEntry,
            GrapheneEvaluationStackMapKeyEntry,
            GrapheneEvaluationStackMapValueEntry,
        )
        name = "EvaluationStackEntry"

    @staticmethod
    def from_native_entry(entry):
        if isinstance(entry, EvaluationStackPathEntry):
            return GrapheneEvaluationStackPathEntry(field_name=entry.field_name)
        elif isinstance(entry, EvaluationStackListItemEntry):
            return GrapheneEvaluationStackListItemEntry(list_index=entry.list_index)
        elif isinstance(entry, EvaluationStackMapKeyEntry):
            return GrapheneEvaluationStackMapKeyEntry(map_key=entry.map_key)
        elif isinstance(entry, EvaluationStackMapValueEntry):
            return GrapheneEvaluationStackMapValueEntry(map_key=entry.map_key)
        else:
            check.failed(f"Unsupported stack entry type {entry}")


class GrapheneEvaluationStack(graphene.ObjectType):
    entries = non_null_list(lambda: GrapheneEvaluationStackEntry)

    class Meta:
        name = "EvaluationStack"

    def __init__(self, config_schema_snapshot, stack):
        self._config_schema_snapshot = check.inst_param(
            config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot
        )
        self._stack = stack
        super().__init__()

    def resolve_entries(self, _):
        return map(GrapheneEvaluationStackEntry.from_native_entry, self._stack.entries)


class GrapheneEvaluationErrorReason(graphene.Enum):
    RUNTIME_TYPE_MISMATCH = "RUNTIME_TYPE_MISMATCH"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    MISSING_REQUIRED_FIELDS = "MISSING_REQUIRED_FIELDS"
    FIELD_NOT_DEFINED = "FIELD_NOT_DEFINED"
    FIELDS_NOT_DEFINED = "FIELDS_NOT_DEFINED"
    SELECTOR_FIELD_ERROR = "SELECTOR_FIELD_ERROR"

    class Meta:
        name = "EvaluationErrorReason"


class GraphenePipelineConfigValidationError(graphene.Interface):
    message = graphene.NonNull(graphene.String)
    path = non_null_list(graphene.String)
    stack = graphene.NonNull(GrapheneEvaluationStack)
    reason = graphene.NonNull(GrapheneEvaluationErrorReason)

    class Meta:
        name = "PipelineConfigValidationError"

    @staticmethod
    def from_dagster_error(config_schema_snapshot, error):
        check.inst_param(config_schema_snapshot, "config_schema_snapshot", ConfigSchemaSnapshot)
        check.inst_param(error, "error", DagsterEvaluationError)

        if isinstance(error.error_data, RuntimeMismatchErrorData):
            return GrapheneRuntimeMismatchConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=GrapheneEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason.value,
                value_rep=error.error_data.value_rep,
            )
        elif isinstance(error.error_data, MissingFieldErrorData):
            return GrapheneMissingFieldConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=GrapheneEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason.value,
                field=GrapheneConfigTypeField(
                    config_schema_snapshot=config_schema_snapshot,
                    field_snap=error.error_data.field_snap,
                ),
            )
        elif isinstance(error.error_data, MissingFieldsErrorData):
            return GrapheneMissingFieldsConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=GrapheneEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason.value,
                fields=[
                    GrapheneConfigTypeField(
                        config_schema_snapshot=config_schema_snapshot,
                        field_snap=field_snap,
                    )
                    for field_snap in error.error_data.field_snaps
                ],
            )

        elif isinstance(error.error_data, FieldNotDefinedErrorData):
            return GrapheneFieldNotDefinedConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=GrapheneEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason.value,
                field_name=error.error_data.field_name,
            )
        elif isinstance(error.error_data, FieldsNotDefinedErrorData):
            return GrapheneFieldsNotDefinedConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=GrapheneEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason.value,
                field_names=error.error_data.field_names,
            )
        elif isinstance(error.error_data, SelectorTypeErrorData):
            return GrapheneSelectorTypeConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=GrapheneEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason.value,
                incoming_fields=error.error_data.incoming_fields,
            )
        else:
            check.failed(
                "Error type not supported {error_data}".format(error_data=repr(error.error_data))
            )


class GrapheneRuntimeMismatchConfigError(graphene.ObjectType):
    value_rep = graphene.Field(graphene.String)

    class Meta:
        interfaces = (GraphenePipelineConfigValidationError,)
        name = "RuntimeMismatchConfigError"


class GrapheneMissingFieldConfigError(graphene.ObjectType):
    field = graphene.NonNull(GrapheneConfigTypeField)

    class Meta:
        interfaces = (GraphenePipelineConfigValidationError,)
        name = "MissingFieldConfigError"


class GrapheneMissingFieldsConfigError(graphene.ObjectType):
    fields = non_null_list(GrapheneConfigTypeField)

    class Meta:
        interfaces = (GraphenePipelineConfigValidationError,)
        name = "MissingFieldsConfigError"


class GrapheneFieldNotDefinedConfigError(graphene.ObjectType):
    field_name = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (GraphenePipelineConfigValidationError,)
        name = "FieldNotDefinedConfigError"


class GrapheneFieldsNotDefinedConfigError(graphene.ObjectType):
    field_names = non_null_list(graphene.String)

    class Meta:
        interfaces = (GraphenePipelineConfigValidationError,)
        name = "FieldsNotDefinedConfigError"


class GrapheneSelectorTypeConfigError(graphene.ObjectType):
    incoming_fields = non_null_list(graphene.String)

    class Meta:
        interfaces = (GraphenePipelineConfigValidationError,)
        name = "SelectorTypeConfigError"


ERROR_DATA_TYPES = (
    FieldNotDefinedErrorData,
    FieldsNotDefinedErrorData,
    MissingFieldErrorData,
    MissingFieldsErrorData,
    RuntimeMismatchErrorData,
    SelectorTypeErrorData,
    SerializableErrorInfo,
)


class EvaluationError(namedtuple("_EvaluationError", "stack reason message error_data")):
    def __new__(cls, stack, reason, message, error_data):
        return super().__new__(
            cls,
            check.inst_param(stack, "stack", GrapheneEvaluationStack),
            check.inst_param(reason, "reason", GrapheneEvaluationErrorReason),
            check.str_param(message, "message"),
            check.inst_param(error_data, "error_data", ERROR_DATA_TYPES),
        )


class GraphenePipelineConfigValidationValid(graphene.ObjectType):
    pipeline_name = graphene.NonNull(graphene.String)

    class Meta:
        name = "PipelineConfigValidationValid"


class GraphenePipelineConfigValidationInvalid(graphene.Interface):
    pipeline_name = graphene.NonNull(graphene.String)
    errors = non_null_list(GraphenePipelineConfigValidationError)

    class Meta:
        name = "PipelineConfigValidationInvalid"


class GrapheneRunConfigValidationInvalid(graphene.ObjectType):
    pipeline_name = graphene.NonNull(graphene.String)
    errors = non_null_list(GraphenePipelineConfigValidationError)

    class Meta:
        interfaces = (GraphenePipelineConfigValidationInvalid,)
        name = "RunConfigValidationInvalid"

    @staticmethod
    def for_validation_errors(represented_pipeline, errors):
        check.inst_param(represented_pipeline, "represented_pipeline", RepresentedPipeline)
        check.list_param(errors, "errors", of_type=DagsterEvaluationError)
        return GrapheneRunConfigValidationInvalid(
            pipeline_name=represented_pipeline.name,
            errors=[
                GraphenePipelineConfigValidationError.from_dagster_error(
                    represented_pipeline.config_schema_snapshot, err
                )
                for err in errors
            ],
        )
