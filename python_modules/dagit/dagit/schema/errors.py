from __future__ import absolute_import
import traceback
import graphene

from dagster import check
import dagster.core.evaluator
from dagit.schema import pipelines, execution, runs
from .utils import non_null_list


class Error(graphene.Interface):
    message = graphene.String(required=True)
    stack = non_null_list(graphene.String)


class PythonError(graphene.ObjectType):
    def __init__(self, exc_type, exc_value, exc_tb):
        super(PythonError, self).__init__()
        self.message = traceback.format_exception_only(exc_type, exc_value)[0]
        self.stack = traceback.format_tb(tb=exc_tb)

    class Meta:
        interfaces = (Error, )


class PipelineNotFoundError(graphene.ObjectType):
    pipeline_name = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (Error, )

    def __init__(self, pipeline_name):
        super(PipelineNotFoundError, self).__init__()
        self.pipeline_name = check.str_param(pipeline_name, 'pipeline_name')
        self.message = 'Pipeline {pipeline_name} does not exist'.format(pipeline_name=pipeline_name)


class PipelineConfigValidationValid(graphene.ObjectType):
    pipeline = graphene.Field(graphene.NonNull(lambda: pipelines.GraphenePipeline))


class PipelineConfigValidationInvalid(graphene.ObjectType):
    pipeline = graphene.Field(graphene.NonNull(lambda: pipelines.GraphenePipeline))
    errors = non_null_list(lambda: PipelineConfigValidationError)


class PipelineConfigValidationResult(graphene.Union):
    class Meta:
        types = (
            PipelineConfigValidationValid,
            PipelineConfigValidationInvalid,
            PipelineNotFoundError,
        )


class PipelineConfigValidationError(graphene.Interface):
    message = graphene.NonNull(graphene.String)
    path = non_null_list(graphene.String)
    stack = graphene.NonNull(lambda: EvaluationStack)
    reason = graphene.NonNull(lambda: EvaluationErrorReason)


class RuntimeMismatchConfigError(graphene.ObjectType):
    type = graphene.NonNull(lambda: pipelines.GrapheneDagsterType)
    value_rep = graphene.Field(graphene.String)

    class Meta:
        interfaces = (PipelineConfigValidationError, )

    def resolve_type(self, _info):
        return pipelines.GrapheneDagsterType.from_dagster_type(self.type)


class MissingFieldConfigError(graphene.ObjectType):
    field = graphene.NonNull(lambda: pipelines.TypeField)

    class Meta:
        interfaces = (PipelineConfigValidationError, )


class FieldNotDefinedConfigError(graphene.ObjectType):
    field_name = graphene.NonNull(graphene.String)

    class Meta:
        interfaces = (PipelineConfigValidationError, )


class SelectorTypeConfigError(graphene.ObjectType):
    incoming_fields = non_null_list(graphene.String)

    class Meta:
        interfaces = (PipelineConfigValidationError, )


class RuntimeMismatchErrorData(graphene.ObjectType):
    type = graphene.NonNull(lambda: pipelines.GrapheneDagsterType)
    value_rep = graphene.Field(graphene.String)

    def resolve_type(self, _info):
        return pipelines.GrapheneDagsterType.from_dagster_type(self.type)


class MissingFieldErrorData(graphene.ObjectType):
    field = graphene.NonNull(lambda: pipelines.TypeField)


class FieldNotDefinedErrorData(graphene.ObjectType):
    field_name = graphene.NonNull(graphene.String)


class SelectorTypeErrorData(graphene.ObjectType):
    incoming_fields = non_null_list(graphene.String)


class EvaluationErrorReason(graphene.Enum):

    RUNTIME_TYPE_MISMATCH = 'RUNTIME_TYPE_MISMATCH'
    MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD'
    FIELD_NOT_DEFINED = 'FIELD_NOT_DEFINED'
    SELECTOR_FIELD_ERROR = 'SELECTOR_FIELD_ERROR'


class EvaluationStackListItemEntry(graphene.ObjectType):
    def __init__(self, list_index):
        super(EvaluationStackListItemEntry, self).__init__()
        self._list_index = list_index

    list_index = graphene.NonNull(graphene.Int)

    def resolve_list_index(self, _info):
        return self._list_index


class EvaluationStackPathEntry(graphene.ObjectType):
    def __init__(self, field_name, field_def):
        super(EvaluationStackPathEntry, self).__init__()
        self._field_name = field_name
        self._field_def = field_def

    field = graphene.NonNull(lambda: pipelines.TypeField)

    def resolve_field(self, _info):
        return pipelines.TypeField(name=self._field_name, field=self._field_def)  # pylint: disable=E1101


class EvaluationStackEntry(graphene.Union):
    class Meta:
        types = (EvaluationStackListItemEntry, EvaluationStackPathEntry)

    @staticmethod
    def from_native_entry(entry):
        if isinstance(entry, dagster.core.evaluator.EvaluationStackPathEntry):
            return EvaluationStackPathEntry(
                field_name=entry.field_name,
                field_def=entry.field_def,
            )
        elif isinstance(entry, dagster.core.evaluator.EvaluationStackListItemEntry):
            return EvaluationStackListItemEntry(list_index=entry.list_index)
        else:
            check.failed('Unsupported stack entry type {entry}'.format(entry=entry))


class EvaluationStack(graphene.ObjectType):
    entries = non_null_list(EvaluationStackEntry)

    def resolve_entries(self, _info):
        return map(EvaluationStackEntry.from_native_entry, self.entries)


class ConfigErrorData(graphene.Union):
    class Meta:
        types = (
            RuntimeMismatchErrorData,
            MissingFieldErrorData,
            FieldNotDefinedErrorData,
            SelectorTypeErrorData,
        )

    @staticmethod
    def from_dagster_error(error):
        check.inst_param(error, 'error', dagster.core.evaluator.EvaluationError)

        if isinstance(error.error_data, dagster.core.evaluator.RuntimeMismatchErrorData):
            return RuntimeMismatchConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=error.stack,
                reason=error.reason,
                type=error.error_data.dagster_type,
                value_rep=error.error_data.value_rep,
            )
        elif isinstance(error.error_data, dagster.core.evaluator.MissingFieldErrorData):
            return MissingFieldConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=error.stack,
                reason=error.reason,
                field=pipelines.TypeField(
                    name=error.error_data.field_name, field=error.error_data.field_def
                ),
            )
        elif isinstance(error.error_data, dagster.core.evaluator.FieldNotDefinedErrorData):
            return FieldNotDefinedConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=error.stack,
                reason=error.reason,
                field_name=error.error_data.field_name,
            )
        elif isinstance(error.error_data, dagster.core.evaluator.SelectorTypeErrorData):
            return SelectorTypeConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=error.stack,
                reason=error.reason,
                incoming_fields=error.error_data.incoming_fields,
            )
        else:
            check.failed(
                'Error type not supported {error_data}'.format(error_data=repr(error.error_data))
            )


class PipelineOrError(graphene.Union):
    class Meta:
        types = (pipelines.GraphenePipeline, PythonError, PipelineNotFoundError)


class PipelinesOrError(graphene.Union):
    class Meta:
        types = (pipelines.PipelineConnection, PythonError)


class ExecutionPlanResult(graphene.Union):
    class Meta:
        types = (execution.ExecutionPlan, PipelineConfigValidationInvalid, PipelineNotFoundError)


class StartPipelineExecutionSuccess(graphene.ObjectType):
    run = graphene.Field(graphene.NonNull(lambda: runs.PipelineRun))


class StartPipelineExecutionResult(graphene.Union):
    class Meta:
        types = (
            StartPipelineExecutionSuccess,
            PipelineConfigValidationInvalid,
            PipelineNotFoundError,
        )
