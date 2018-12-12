from __future__ import absolute_import
import traceback

from dagster import check
import dagster.core.evaluator

from dagster.utils.error import (
    SerializableErrorInfo,
    serializable_error_info_from_exc_info,
)

from dagit.schema import dauphin


class DauphinError(dauphin.Interface):
    class Meta:
        name = 'Error'

    message = dauphin.String(required=True)
    stack = dauphin.non_null_list(dauphin.String)


class DauphinPythonError(dauphin.ObjectType):
    class Meta:
        name = 'PythonError'
        interfaces = (DauphinError, )

    def __init__(self, error_info):
        super(DauphinPythonError, self).__init__()
        check.inst_param(error_info, 'error_info', SerializableErrorInfo)
        self.message = error_info.message
        self.stack = error_info.stack


class DauphinPipelineNotFoundError(dauphin.ObjectType):
    class Meta:
        name = 'PipelineNotFoundError'
        interfaces = (DauphinError, )

    pipeline_name = dauphin.NonNull(dauphin.String)

    def __init__(self, pipeline_name):
        super(DauphinPipelineNotFoundError, self).__init__()
        self.pipeline_name = check.str_param(pipeline_name, 'pipeline_name')
        self.message = 'Pipeline {pipeline_name} does not exist'.format(pipeline_name=pipeline_name)


class PipelineConfigValidationValid(dauphin.ObjectType):
    pipeline = dauphin.Field(dauphin.NonNull('Pipeline'))


class PipelineConfigValidationInvalid(dauphin.ObjectType):
    pipeline = dauphin.Field(dauphin.NonNull('Pipeline'))
    errors = dauphin.non_null_list('PipelineConfigValidationError')


class PipelineConfigValidationResult(dauphin.Union):
    class Meta:
        types = (
            PipelineConfigValidationValid,
            PipelineConfigValidationInvalid,
            DauphinPipelineNotFoundError,
        )


class PipelineConfigValidationError(dauphin.Interface):
    message = dauphin.NonNull(dauphin.String)
    path = dauphin.non_null_list(dauphin.String)
    stack = dauphin.NonNull('EvaluationStack')
    reason = dauphin.NonNull('EvaluationErrorReason')

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


class RuntimeMismatchConfigError(dauphin.ObjectType):
    type = dauphin.NonNull('Type')
    value_rep = dauphin.Field(dauphin.String)

    class Meta:
        interfaces = (PipelineConfigValidationError, )

    def resolve_type(self, info):
        return info.schema.Type.from_dagster_type(info, self.type)


class MissingFieldConfigError(dauphin.ObjectType):
    field = dauphin.NonNull('TypeField')

    class Meta:
        interfaces = (PipelineConfigValidationError, )


class FieldNotDefinedConfigError(dauphin.ObjectType):
    field_name = dauphin.NonNull(dauphin.String)

    class Meta:
        interfaces = (PipelineConfigValidationError, )


class SelectorTypeConfigError(dauphin.ObjectType):
    incoming_fields = dauphin.non_null_list(dauphin.String)

    class Meta:
        interfaces = (PipelineConfigValidationError, )


class EvaluationErrorReason(dauphin.Enum):

    RUNTIME_TYPE_MISMATCH = 'RUNTIME_TYPE_MISMATCH'
    MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD'
    FIELD_NOT_DEFINED = 'FIELD_NOT_DEFINED'
    SELECTOR_FIELD_ERROR = 'SELECTOR_FIELD_ERROR'


class EvaluationStackListItemEntry(dauphin.ObjectType):
    def __init__(self, list_index):
        super(EvaluationStackListItemEntry, self).__init__()
        self._list_index = list_index

    list_index = dauphin.NonNull(dauphin.Int)

    def resolve_list_index(self, _info):
        return self._list_index


class EvaluationStackPathEntry(dauphin.ObjectType):
    def __init__(self, field_name, field_def):
        super(EvaluationStackPathEntry, self).__init__()
        self._field_name = field_name
        self._field_def = field_def

    field = dauphin.NonNull('TypeField')

    def resolve_field(self, info):
        return info.schema.TypeField(name=self._field_name, field=self._field_def)  # pylint: disable=E1101


class EvaluationStackEntry(dauphin.Union):
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


class EvaluationStack(dauphin.ObjectType):
    entries = dauphin.non_null_list('EvaluationStackEntry')

    def resolve_entries(self, info):
        return map(info.schema.EvaluationStackEntry.from_native_entry, self.entries)


class PipelineOrError(dauphin.Union):
    class Meta:
        types = ('Pipeline', DauphinPythonError, DauphinPipelineNotFoundError)


class PipelinesOrError(dauphin.Union):
    class Meta:
        types = ('PipelineConnection', DauphinPythonError)


class ExecutionPlanResult(dauphin.Union):
    class Meta:
        types = ('ExecutionPlan', PipelineConfigValidationInvalid, DauphinPipelineNotFoundError)


class StartPipelineExecutionSuccess(dauphin.ObjectType):
    run = dauphin.Field(dauphin.NonNull('PipelineRun'))


class StartPipelineExecutionResult(dauphin.Union):
    class Meta:
        types = (
            StartPipelineExecutionSuccess,
            PipelineConfigValidationInvalid,
            DauphinPipelineNotFoundError,
        )
