from __future__ import absolute_import
import traceback

from dagster import check
import dagster.core.evaluator

from dagster.utils.error import (
    SerializableErrorInfo,
    serializable_error_info_from_exc_info,
)

from dagit.schema import dauphene


class Error(dauphene.Interface):
    message = dauphene.String(required=True)
    stack = dauphene.non_null_list(dauphene.String)


class PythonError(dauphene.ObjectType):
    def __init__(self, error_info):
        super(PythonError, self).__init__()
        check.inst_param(error_info, 'error_info', SerializableErrorInfo)
        self.message = error_info.message
        self.stack = error_info.stack

    class Meta:
        interfaces = (Error, )


class PipelineNotFoundError(dauphene.ObjectType):
    pipeline_name = dauphene.NonNull(dauphene.String)

    class Meta:
        interfaces = (Error, )

    def __init__(self, pipeline_name):
        super(PipelineNotFoundError, self).__init__()
        self.pipeline_name = check.str_param(pipeline_name, 'pipeline_name')
        self.message = 'Pipeline {pipeline_name} does not exist'.format(pipeline_name=pipeline_name)


class PipelineConfigValidationValid(dauphene.ObjectType):
    pipeline = dauphene.Field(dauphene.NonNull('Pipeline'))


class PipelineConfigValidationInvalid(dauphene.ObjectType):
    pipeline = dauphene.Field(dauphene.NonNull('Pipeline'))
    errors = dauphene.non_null_list('PipelineConfigValidationError')


class PipelineConfigValidationResult(dauphene.Union):
    class Meta:
        types = (
            PipelineConfigValidationValid,
            PipelineConfigValidationInvalid,
            PipelineNotFoundError,
        )


class PipelineConfigValidationError(dauphene.Interface):
    message = dauphene.NonNull(dauphene.String)
    path = dauphene.non_null_list(dauphene.String)
    stack = dauphene.NonNull('EvaluationStack')
    reason = dauphene.NonNull('EvaluationErrorReason')

    @staticmethod
    def from_dagster_error(info, error):
        check.inst_param(error, 'error', dagster.core.evaluator.EvaluationError)

        if isinstance(error.error_data, dagster.core.evaluator.RuntimeMismatchErrorData):
            return info.schema.RuntimeMismatchConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=error.stack,
                reason=error.reason,
                type=error.error_data.dagster_type,
                value_rep=error.error_data.value_rep,
            )
        elif isinstance(error.error_data, dagster.core.evaluator.MissingFieldErrorData):
            return info.schema.MissingFieldConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=error.stack,
                reason=error.reason,
                field=info.schema.TypeField(
                    name=error.error_data.field_name, field=error.error_data.field_def
                ),
            )
        elif isinstance(error.error_data, dagster.core.evaluator.FieldNotDefinedErrorData):
            return info.schema.FieldNotDefinedConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=error.stack,
                reason=error.reason,
                field_name=error.error_data.field_name,
            )
        elif isinstance(error.error_data, dagster.core.evaluator.SelectorTypeErrorData):
            return info.schema.SelectorTypeConfigError(
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


class RuntimeMismatchConfigError(dauphene.ObjectType):
    type = dauphene.NonNull('Type')
    value_rep = dauphene.Field(dauphene.String)

    class Meta:
        interfaces = (PipelineConfigValidationError, )

    def resolve_type(self, info):
        return info.schema.Type.from_dagster_type(info, self.type)


class MissingFieldConfigError(dauphene.ObjectType):
    field = dauphene.NonNull('TypeField')

    class Meta:
        interfaces = (PipelineConfigValidationError, )


class FieldNotDefinedConfigError(dauphene.ObjectType):
    field_name = dauphene.NonNull(dauphene.String)

    class Meta:
        interfaces = (PipelineConfigValidationError, )


class SelectorTypeConfigError(dauphene.ObjectType):
    incoming_fields = dauphene.non_null_list(dauphene.String)

    class Meta:
        interfaces = (PipelineConfigValidationError, )


class EvaluationErrorReason(dauphene.Enum):

    RUNTIME_TYPE_MISMATCH = 'RUNTIME_TYPE_MISMATCH'
    MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD'
    FIELD_NOT_DEFINED = 'FIELD_NOT_DEFINED'
    SELECTOR_FIELD_ERROR = 'SELECTOR_FIELD_ERROR'


class EvaluationStackListItemEntry(dauphene.ObjectType):
    def __init__(self, list_index):
        super(EvaluationStackListItemEntry, self).__init__()
        self._list_index = list_index

    list_index = dauphene.NonNull(dauphene.Int)

    def resolve_list_index(self, _info):
        return self._list_index


class EvaluationStackPathEntry(dauphene.ObjectType):
    def __init__(self, field_name, field_def):
        super(EvaluationStackPathEntry, self).__init__()
        self._field_name = field_name
        self._field_def = field_def

    field = dauphene.NonNull('TypeField')

    def resolve_field(self, info):
        return info.schema.TypeField(name=self._field_name, field=self._field_def)  # pylint: disable=E1101


class EvaluationStackEntry(dauphene.Union):
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


class EvaluationStack(dauphene.ObjectType):
    entries = dauphene.non_null_list('EvaluationStackEntry')

    def resolve_entries(self, info):
        return map(info.schema.EvaluationStackEntry.from_native_entry, self.entries)


class PipelineOrError(dauphene.Union):
    class Meta:
        types = ('Pipeline', PythonError, PipelineNotFoundError)


class PipelinesOrError(dauphene.Union):
    class Meta:
        types = ('PipelineConnection', PythonError)


class ExecutionPlanResult(dauphene.Union):
    class Meta:
        types = ('ExecutionPlan', PipelineConfigValidationInvalid, PipelineNotFoundError)


class StartPipelineExecutionSuccess(dauphene.ObjectType):
    run = dauphene.Field(dauphene.NonNull('PipelineRun'))


class StartPipelineExecutionResult(dauphene.Union):
    class Meta:
        types = (
            StartPipelineExecutionSuccess,
            PipelineConfigValidationInvalid,
            PipelineNotFoundError,
        )
