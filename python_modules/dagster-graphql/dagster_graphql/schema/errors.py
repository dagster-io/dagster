from __future__ import absolute_import

from dagster import check

from dagster.core.types.evaluator.errors import (
    EvaluationError,
    MissingFieldErrorData,
    MissingFieldsErrorData,
    FieldNotDefinedErrorData,
    FieldsNotDefinedErrorData,
    RuntimeMismatchErrorData,
    SelectorTypeErrorData,
)
from dagster.core.types.evaluator.stack import (
    EvaluationStackPathEntry,
    EvaluationStackListItemEntry,
)

from dagster.utils.error import SerializableErrorInfo

from dagster_graphql import dauphin

from .config_types import to_dauphin_config_type
from .runs import DauphinStepEvent


class DauphinError(dauphin.Interface):
    class Meta:
        name = 'Error'

    message = dauphin.String(required=True)
    stack = dauphin.non_null_list(dauphin.String)


class DauphinPythonError(dauphin.ObjectType):
    class Meta:
        name = 'PythonError'
        interfaces = (DauphinError,)

    def __init__(self, error_info):
        super(DauphinPythonError, self).__init__()
        check.inst_param(error_info, 'error_info', SerializableErrorInfo)
        self.message = error_info.message
        self.stack = error_info.stack


class DauphinPipelineNotFoundError(dauphin.ObjectType):
    class Meta:
        name = 'PipelineNotFoundError'
        interfaces = (DauphinError,)

    pipeline_name = dauphin.NonNull(dauphin.String)

    def __init__(self, pipeline_name):
        super(DauphinPipelineNotFoundError, self).__init__()
        self.pipeline_name = check.str_param(pipeline_name, 'pipeline_name')
        self.message = 'Pipeline {pipeline_name} does not exist'.format(pipeline_name=pipeline_name)


class DauphinPipelineRunNotFoundError(dauphin.ObjectType):
    class Meta:
        name = 'PipelineRunNotFoundError'
        interfaces = (DauphinError,)

    run_id = dauphin.NonNull(dauphin.String)

    def __init__(self, run_id):
        super(DauphinPipelineRunNotFoundError, self).__init__()
        self.run_id = check.str_param(run_id, 'run_id')
        self.message = 'Pipeline run {run_id} does not exist'.format(run_id=run_id)


class DauphinSolidNotFoundError(dauphin.ObjectType):
    class Meta:
        name = 'SolidNotFoundError'
        interfaces = (DauphinError,)

    solid_name = dauphin.NonNull(dauphin.String)

    def __init__(self, solid_name):
        super(DauphinSolidNotFoundError, self).__init__()
        self.solid_name = check.str_param(solid_name, 'solid_name')
        self.message = 'Solid {solid_name} does not exist'.format(solid_name=solid_name)


class DauphinModeNotFoundError(dauphin.ObjectType):
    class Meta:
        name = 'ModeNotFoundError'
        interfaces = (DauphinError,)

    mode = dauphin.NonNull(dauphin.String)

    def __init__(self, mode, selector):
        self.mode = check.str_param(mode, 'mode')
        self.message = 'Mode {mode} not found in pipeline {pipeline}.'.format(
            mode=mode, pipeline=selector.name
        )


class DauphinInvalidDefinitionError(dauphin.ObjectType):
    class Meta:
        name = 'InvalidDefinitionError'
        interfaces = (DauphinError,)

    def __init__(self, error_info):
        super(DauphinInvalidDefinitionError, self).__init__()
        check.inst_param(error_info, 'error_info', SerializableErrorInfo)
        self.message = error_info.message
        self.stack = error_info.stack


class DauphinPipelineConfigValidationValid(dauphin.ObjectType):
    class Meta:
        name = 'PipelineConfigValidationValid'

    pipeline = dauphin.Field(dauphin.NonNull('Pipeline'))


class DauphinPipelineConfigValidationInvalid(dauphin.ObjectType):
    class Meta:
        name = 'PipelineConfigValidationInvalid'

    pipeline = dauphin.Field(dauphin.NonNull('Pipeline'))
    errors = dauphin.non_null_list('PipelineConfigValidationError')


class DauphinPipelineConfigValidationResult(dauphin.Union):
    class Meta:
        name = 'PipelineConfigValidationResult'
        types = (
            DauphinPipelineConfigValidationValid,
            DauphinPipelineConfigValidationInvalid,
            DauphinPipelineNotFoundError,
        )


class DauphinPipelineConfigValidationError(dauphin.Interface):
    class Meta:
        name = 'PipelineConfigValidationError'

    message = dauphin.NonNull(dauphin.String)
    path = dauphin.non_null_list(dauphin.String)
    stack = dauphin.NonNull('EvaluationStack')
    reason = dauphin.NonNull('EvaluationErrorReason')

    @staticmethod
    def from_dagster_error(graphene_info, error):
        check.inst_param(error, 'error', EvaluationError)

        if isinstance(error.error_data, RuntimeMismatchErrorData):
            return graphene_info.schema.type_named('RuntimeMismatchConfigError')(
                message=error.message,
                path=[],  # TODO: remove
                stack=error.stack,
                reason=error.reason,
                type=error.error_data.config_type,
                value_rep=error.error_data.value_rep,
            )
        elif isinstance(error.error_data, MissingFieldErrorData):
            return graphene_info.schema.type_named('MissingFieldConfigError')(
                message=error.message,
                path=[],  # TODO: remove
                stack=error.stack,
                reason=error.reason,
                field=graphene_info.schema.type_named('ConfigTypeField')(
                    name=error.error_data.field_name, field=error.error_data.field_def
                ),
            )
        elif isinstance(error.error_data, MissingFieldsErrorData):
            return graphene_info.schema.type_named('MissingFieldsConfigError')(
                message=error.message,
                path=[],  # TODO: remove
                stack=error.stack,
                reason=error.reason,
                fields=[
                    graphene_info.schema.type_named('ConfigTypeField')(
                        name=field_name, field=field_def
                    )
                    for field_name, field_def in zip(
                        error.error_data.field_names, error.error_data.field_defs
                    )
                ],
            )

        elif isinstance(error.error_data, FieldNotDefinedErrorData):
            return graphene_info.schema.type_named('FieldNotDefinedConfigError')(
                message=error.message,
                path=[],  # TODO: remove
                stack=error.stack,
                reason=error.reason,
                field_name=error.error_data.field_name,
            )
        elif isinstance(error.error_data, FieldsNotDefinedErrorData):
            return graphene_info.schema.type_named('FieldsNotDefinedConfigError')(
                message=error.message,
                path=[],  # TODO: remove
                stack=error.stack,
                reason=error.reason,
                field_names=error.error_data.field_names,
            )
        elif isinstance(error.error_data, SelectorTypeErrorData):
            return graphene_info.schema.type_named('SelectorTypeConfigError')(
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


class DauphinRuntimeMismatchConfigError(dauphin.ObjectType):
    class Meta:
        name = 'RuntimeMismatchConfigError'
        interfaces = (DauphinPipelineConfigValidationError,)

    type = dauphin.NonNull('ConfigType')
    value_rep = dauphin.Field(dauphin.String)

    def resolve_type(self, _info):
        return to_dauphin_config_type(self.type)


class DauphinMissingFieldConfigError(dauphin.ObjectType):
    class Meta:
        name = 'MissingFieldConfigError'
        interfaces = (DauphinPipelineConfigValidationError,)

    field = dauphin.NonNull('ConfigTypeField')


class DauphinMissingFieldsConfigError(dauphin.ObjectType):
    class Meta:
        name = 'MissingFieldsConfigError'
        interfaces = (DauphinPipelineConfigValidationError,)

    fields = dauphin.non_null_list('ConfigTypeField')


class DauphinFieldNotDefinedConfigError(dauphin.ObjectType):
    class Meta:
        name = 'FieldNotDefinedConfigError'
        interfaces = (DauphinPipelineConfigValidationError,)

    field_name = dauphin.NonNull(dauphin.String)


class DauphinFieldsNotDefinedConfigError(dauphin.ObjectType):
    class Meta:
        name = 'FieldsNotDefinedConfigError'
        interfaces = (DauphinPipelineConfigValidationError,)

    field_names = dauphin.non_null_list(dauphin.String)


class DauphinSelectorTypeConfigError(dauphin.ObjectType):
    class Meta:
        name = 'SelectorTypeConfigError'
        interfaces = (DauphinPipelineConfigValidationError,)

    incoming_fields = dauphin.non_null_list(dauphin.String)


class DauphinEvaluationErrorReason(dauphin.Enum):
    class Meta:
        name = 'EvaluationErrorReason'

    RUNTIME_TYPE_MISMATCH = 'RUNTIME_TYPE_MISMATCH'
    MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD'
    MISSING_REQUIRED_FIELDS = 'MISSING_REQUIRED_FIELDS'
    FIELD_NOT_DEFINED = 'FIELD_NOT_DEFINED'
    FIELDS_NOT_DEFINED = 'FIELDS_NOT_DEFINED'
    SELECTOR_FIELD_ERROR = 'SELECTOR_FIELD_ERROR'


class DauphinEvaluationStackListItemEntry(dauphin.ObjectType):
    class Meta:
        name = 'EvaluationStackListItemEntry'

    def __init__(self, list_index):
        super(DauphinEvaluationStackListItemEntry, self).__init__()
        self._list_index = list_index

    list_index = dauphin.NonNull(dauphin.Int)

    def resolve_list_index(self, _info):
        return self._list_index


class DauphinEvaluationStackPathEntry(dauphin.ObjectType):
    class Meta:
        name = 'EvaluationStackPathEntry'

    def __init__(self, field_name, field_def):
        super(DauphinEvaluationStackPathEntry, self).__init__()
        self._field_name = field_name
        self._field_def = field_def

    field = dauphin.NonNull('ConfigTypeField')

    def resolve_field(self, info):
        return info.schema.type_named('ConfigTypeField')(
            name=self._field_name, field=self._field_def
        )  # pylint: disable=E1101


class DauphinEvaluationStackEntry(dauphin.Union):
    class Meta:
        name = 'EvaluationStackEntry'
        types = (DauphinEvaluationStackListItemEntry, DauphinEvaluationStackPathEntry)

    @staticmethod
    def from_native_entry(entry):
        if isinstance(entry, EvaluationStackPathEntry):
            return DauphinEvaluationStackPathEntry(
                field_name=entry.field_name, field_def=entry.field_def
            )
        elif isinstance(entry, EvaluationStackListItemEntry):
            return DauphinEvaluationStackListItemEntry(list_index=entry.list_index)
        else:
            check.failed('Unsupported stack entry type {entry}'.format(entry=entry))


class DauphinEvaluationStack(dauphin.ObjectType):
    class Meta:
        name = 'EvaluationStack'

    entries = dauphin.non_null_list('EvaluationStackEntry')

    def resolve_entries(self, graphene_info):
        return map(
            graphene_info.schema.type_named('EvaluationStackEntry').from_native_entry, self.entries
        )


class DauphinPipelineOrError(dauphin.Union):
    class Meta:
        name = 'PipelineOrError'
        types = (
            'Pipeline',
            DauphinPythonError,
            DauphinPipelineNotFoundError,
            DauphinSolidNotFoundError,
        )


class DauphinPipelinesOrError(dauphin.Union):
    class Meta:
        name = 'PipelinesOrError'
        types = ('PipelineConnection', DauphinPythonError, DauphinInvalidDefinitionError)


class DauphinExecutionPlanResult(dauphin.Union):
    class Meta:
        name = 'ExecutionPlanResult'
        types = (
            'ExecutionPlan',
            DauphinPipelineConfigValidationInvalid,
            DauphinPipelineNotFoundError,
        )


class DauphinStartPipelineExecutionSuccess(dauphin.ObjectType):
    class Meta:
        name = 'StartPipelineExecutionSuccess'

    run = dauphin.Field(dauphin.NonNull('PipelineRun'))


class DauphinInvalidStepError(dauphin.ObjectType):
    class Meta:
        name = 'InvalidStepError'

    invalid_step_key = dauphin.NonNull(dauphin.String)


class DauphinInvalidOutputError(dauphin.ObjectType):
    class Meta:
        name = 'InvalidOutputError'

    step_key = dauphin.NonNull(dauphin.String)
    invalid_output_name = dauphin.NonNull(dauphin.String)


class DauphinStartPipelineExecutionResult(dauphin.Union):
    class Meta:
        name = 'StartPipelineExecutionResult'
        types = (
            DauphinInvalidStepError,
            DauphinInvalidOutputError,
            DauphinPipelineConfigValidationInvalid,
            DauphinPipelineNotFoundError,
            DauphinStartPipelineExecutionSuccess,
        )


class DauphinExecutePlanSuccess(dauphin.ObjectType):
    class Meta:
        name = 'ExecutePlanSuccess'

    pipeline = dauphin.Field(dauphin.NonNull('Pipeline'))
    has_failures = dauphin.Field(dauphin.NonNull(dauphin.Boolean))
    step_events = dauphin.non_null_list(DauphinStepEvent)


class DauphinExecutePlanResult(dauphin.Union):
    class Meta:
        name = 'ExecutePlanResult'
        types = (
            DauphinExecutePlanSuccess,
            DauphinPipelineConfigValidationInvalid,
            DauphinPipelineNotFoundError,
            DauphinInvalidStepError,
            DauphinPythonError,
        )


class DauphinConfigTypeNotFoundError(dauphin.ObjectType):
    class Meta:
        name = 'ConfigTypeNotFoundError'
        interfaces = (DauphinError,)

    pipeline = dauphin.NonNull('Pipeline')
    config_type_name = dauphin.NonNull(dauphin.String)


class DauphinRuntimeTypeNotFoundError(dauphin.ObjectType):
    class Meta:
        name = 'RuntimeTypeNotFoundError'
        interfaces = (DauphinError,)

    pipeline = dauphin.NonNull('Pipeline')
    runtime_type_name = dauphin.NonNull(dauphin.String)


class DauphinConfigTypeOrError(dauphin.Union):
    class Meta:
        name = 'ConfigTypeOrError'
        types = (
            'EnumConfigType',
            'CompositeConfigType',
            'RegularConfigType',
            DauphinPipelineNotFoundError,
            DauphinConfigTypeNotFoundError,
        )


class DauphinRuntimeTypeOrError(dauphin.Union):
    class Meta:
        name = 'RuntimeTypeOrError'
        types = (
            'RegularRuntimeType',
            DauphinPipelineNotFoundError,
            DauphinRuntimeTypeNotFoundError,
        )


class DauphinPipelineRunOrError(dauphin.Union):
    class Meta:
        name = 'PipelineRunOrError'
        types = ('PipelineRun', DauphinPipelineRunNotFoundError)
