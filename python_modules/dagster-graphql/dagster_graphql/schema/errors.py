from __future__ import absolute_import

from dagster_graphql import dauphin

from dagster import check
from dagster.config.errors import (
    EvaluationError,
    FieldNotDefinedErrorData,
    FieldsNotDefinedErrorData,
    MissingFieldErrorData,
    MissingFieldsErrorData,
    RuntimeMismatchErrorData,
    SelectorTypeErrorData,
)
from dagster.config.stack import EvaluationStackListItemEntry, EvaluationStackPathEntry
from dagster.core.snap import ConfigSchemaSnapshot, PipelineIndex
from dagster.utils.error import SerializableErrorInfo

from .config_types import DauphinConfigTypeField
from .runs import DauphinStepEvent


class DauphinError(dauphin.Interface):
    class Meta(object):
        name = 'Error'

    message = dauphin.String(required=True)


class DauphinPythonError(dauphin.ObjectType):
    class Meta(object):
        name = 'PythonError'
        interfaces = (DauphinError,)

    className = dauphin.Field(dauphin.String)
    stack = dauphin.non_null_list(dauphin.String)
    cause = dauphin.Field('PythonError')

    def __init__(self, error_info):
        super(DauphinPythonError, self).__init__()
        check.inst_param(error_info, 'error_info', SerializableErrorInfo)
        self.message = error_info.message
        self.stack = error_info.stack
        self.cause = error_info.cause
        self.className = error_info.cls_name


class DauphinSchedulerNotDefinedError(dauphin.ObjectType):
    class Meta(object):
        name = 'SchedulerNotDefinedError'
        interfaces = (DauphinError,)

    def __init__(self):
        super(DauphinSchedulerNotDefinedError, self).__init__()
        self.message = 'Scheduler is not defined for the currently loaded repository.'


class DauphinScheduleNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = 'ScheduleNotFoundError'
        interfaces = (DauphinError,)

    schedule_name = dauphin.NonNull(dauphin.String)

    def __init__(self, schedule_name):
        super(DauphinScheduleNotFoundError, self).__init__()
        self.schedule_name = check.str_param(schedule_name, 'schedule_name')
        self.message = (
            'Schedule {schedule_name} is not present in the currently loaded repository.'
        ).format(schedule_name=schedule_name)


class DauphinPipelineSnapshotNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineSnapshotNotFoundError'
        interfaces = (DauphinError,)

    snapshot_id = dauphin.NonNull(dauphin.String)

    def __init__(self, snapshot_id):
        super(DauphinPipelineSnapshotNotFoundError, self).__init__()
        self.snapshot_id = check.str_param(snapshot_id, 'snapshot_id')
        self.message = (
            'Pipeline snapshot {snapshot_id} is not present in the current instance.'
        ).format(snapshot_id=snapshot_id)


class DauphinPipelineNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineNotFoundError'
        interfaces = (DauphinError,)

    pipeline_name = dauphin.NonNull(dauphin.String)

    def __init__(self, pipeline_name):
        super(DauphinPipelineNotFoundError, self).__init__()
        self.pipeline_name = check.str_param(pipeline_name, 'pipeline_name')
        self.message = (
            'Pipeline {pipeline_name} is not present in the currently loaded repository.'
        ).format(pipeline_name=pipeline_name)


class DauphinPipelineRunNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineRunNotFoundError'
        interfaces = (DauphinError,)

    run_id = dauphin.NonNull(dauphin.String)

    def __init__(self, run_id):
        super(DauphinPipelineRunNotFoundError, self).__init__()
        self.run_id = check.str_param(run_id, 'run_id')
        self.message = 'Pipeline run {run_id} could not be found.'.format(run_id=run_id)


class DauphinInvalidPipelineRunsFilterError(dauphin.ObjectType):
    class Meta(object):
        name = 'InvalidPipelineRunsFilterError'
        interfaces = (DauphinError,)

    def __init__(self, message):
        super(DauphinInvalidPipelineRunsFilterError, self).__init__()
        self.message = check.str_param(message, 'message')


class DauphinRunGroupNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = 'RunGroupNotFoundError'
        interfaces = (DauphinError,)

    run_id = dauphin.NonNull(dauphin.String)

    def __init__(self, run_id):
        super(DauphinRunGroupNotFoundError, self).__init__()
        self.run_id = check.str_param(run_id, 'run_id')
        self.message = 'Run group of run {run_id} could not be found.'.format(run_id=run_id)


class DauphinInvalidSubsetError(dauphin.ObjectType):
    class Meta(object):
        name = 'InvalidSubsetError'
        interfaces = (DauphinError,)

    pipeline = dauphin.Field(dauphin.NonNull('Pipeline'))

    def __init__(self, message, pipeline):
        super(DauphinInvalidSubsetError, self).__init__()
        self.message = check.str_param(message, 'message')
        self.pipeline = pipeline


class DauphinPresetNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = 'PresetNotFoundError'
        interfaces = (DauphinError,)

    preset = dauphin.NonNull(dauphin.String)

    def __init__(self, preset, selector):
        self.preset = check.str_param(preset, 'preset')
        self.message = 'Preset {preset} not found in pipeline {pipeline}.'.format(
            preset=preset, pipeline=selector.name
        )


class DauphinModeNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = 'ModeNotFoundError'
        interfaces = (DauphinError,)

    mode = dauphin.NonNull(dauphin.String)

    def __init__(self, mode, selector):
        self.mode = check.str_param(mode, 'mode')
        self.message = 'Mode {mode} not found in pipeline {pipeline}.'.format(
            mode=mode, pipeline=selector.name
        )


class DauphinRunLauncherNotDefinedError(dauphin.ObjectType):
    class Meta(object):
        name = 'RunLauncherNotDefinedError'
        interfaces = (DauphinError,)

    def __init__(self):
        super(DauphinRunLauncherNotDefinedError, self).__init__()
        self.message = 'RunLauncher is not defined for the current instance.'


class DauphinStartPipelineRunDisabledError(dauphin.ObjectType):
    class Meta(object):
        name = 'StartPipelineRunDisabledError'
        interfaces = (DauphinError,)

    def __init__(self):
        super(DauphinStartPipelineRunDisabledError, self).__init__()
        self.message = (
            'Starting pipeline execution is disabled on this instance.  Runs can only be initiated '
            'using the configured run launcher.'
        )


class DauphinPipelineConfigValidationValid(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineConfigValidationValid'

    pipeline_name = dauphin.NonNull(dauphin.String)


class DauphinPipelineConfigValidationInvalid(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineConfigValidationInvalid'

    pipeline_name = dauphin.NonNull(dauphin.String)
    errors = dauphin.non_null_list('PipelineConfigValidationError')

    @staticmethod
    def for_validation_errors(pipeline_index, errors):
        check.inst_param(pipeline_index, 'pipeline_index', PipelineIndex)
        check.list_param(errors, 'errors', of_type=EvaluationError)
        return DauphinPipelineConfigValidationInvalid(
            pipeline_name=pipeline_index.name,
            errors=[
                DauphinPipelineConfigValidationError.from_dagster_error(
                    pipeline_index.config_schema_snapshot, err
                )
                for err in errors
            ],
        )


class DauphinPipelineConfigValidationResult(dauphin.Union):
    class Meta(object):
        name = 'PipelineConfigValidationResult'
        types = (
            DauphinInvalidSubsetError,
            DauphinPipelineConfigValidationValid,
            DauphinPipelineConfigValidationInvalid,
            DauphinPipelineNotFoundError,
            DauphinPythonError,
        )


class DauphinPipelineConfigValidationError(dauphin.Interface):
    class Meta(object):
        name = 'PipelineConfigValidationError'

    message = dauphin.NonNull(dauphin.String)
    path = dauphin.non_null_list(dauphin.String)
    stack = dauphin.NonNull('EvaluationStack')
    reason = dauphin.NonNull('EvaluationErrorReason')

    @staticmethod
    def from_dagster_error(config_schema_snapshot, error):
        check.inst_param(config_schema_snapshot, 'config_schema_snapshot', ConfigSchemaSnapshot)
        check.inst_param(error, 'error', EvaluationError)

        if isinstance(error.error_data, RuntimeMismatchErrorData):
            return DauphinRuntimeMismatchConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=DauphinEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason,
                value_rep=error.error_data.value_rep,
            )
        elif isinstance(error.error_data, MissingFieldErrorData):
            return DauphinMissingFieldConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=DauphinEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason,
                field=DauphinConfigTypeField(
                    config_schema_snapshot=config_schema_snapshot,
                    field_snap=error.error_data.field_snap,
                ),
            )
        elif isinstance(error.error_data, MissingFieldsErrorData):
            return DauphinMissingFieldsConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=DauphinEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason,
                fields=[
                    DauphinConfigTypeField(
                        config_schema_snapshot=config_schema_snapshot, field_snap=field_snap,
                    )
                    for field_snap in error.error_data.field_snaps
                ],
            )

        elif isinstance(error.error_data, FieldNotDefinedErrorData):
            return DauphinFieldNotDefinedConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=DauphinEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason,
                field_name=error.error_data.field_name,
            )
        elif isinstance(error.error_data, FieldsNotDefinedErrorData):
            return DauphinFieldsNotDefinedConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=DauphinEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason,
                field_names=error.error_data.field_names,
            )
        elif isinstance(error.error_data, SelectorTypeErrorData):
            return DauphinSelectorTypeConfigError(
                message=error.message,
                path=[],  # TODO: remove
                stack=DauphinEvaluationStack(config_schema_snapshot, error.stack),
                reason=error.reason,
                incoming_fields=error.error_data.incoming_fields,
            )
        else:
            check.failed(
                'Error type not supported {error_data}'.format(error_data=repr(error.error_data))
            )


class DauphinRuntimeMismatchConfigError(dauphin.ObjectType):
    class Meta(object):
        name = 'RuntimeMismatchConfigError'
        interfaces = (DauphinPipelineConfigValidationError,)

    value_rep = dauphin.Field(dauphin.String)


class DauphinMissingFieldConfigError(dauphin.ObjectType):
    class Meta(object):
        name = 'MissingFieldConfigError'
        interfaces = (DauphinPipelineConfigValidationError,)

    field = dauphin.NonNull('ConfigTypeField')


class DauphinMissingFieldsConfigError(dauphin.ObjectType):
    class Meta(object):
        name = 'MissingFieldsConfigError'
        interfaces = (DauphinPipelineConfigValidationError,)

    fields = dauphin.non_null_list('ConfigTypeField')


class DauphinFieldNotDefinedConfigError(dauphin.ObjectType):
    class Meta(object):
        name = 'FieldNotDefinedConfigError'
        interfaces = (DauphinPipelineConfigValidationError,)

    field_name = dauphin.NonNull(dauphin.String)


class DauphinFieldsNotDefinedConfigError(dauphin.ObjectType):
    class Meta(object):
        name = 'FieldsNotDefinedConfigError'
        interfaces = (DauphinPipelineConfigValidationError,)

    field_names = dauphin.non_null_list(dauphin.String)


class DauphinSelectorTypeConfigError(dauphin.ObjectType):
    class Meta(object):
        name = 'SelectorTypeConfigError'
        interfaces = (DauphinPipelineConfigValidationError,)

    incoming_fields = dauphin.non_null_list(dauphin.String)


class DauphinEvaluationErrorReason(dauphin.Enum):
    class Meta(object):
        name = 'EvaluationErrorReason'

    RUNTIME_TYPE_MISMATCH = 'RUNTIME_TYPE_MISMATCH'
    MISSING_REQUIRED_FIELD = 'MISSING_REQUIRED_FIELD'
    MISSING_REQUIRED_FIELDS = 'MISSING_REQUIRED_FIELDS'
    FIELD_NOT_DEFINED = 'FIELD_NOT_DEFINED'
    FIELDS_NOT_DEFINED = 'FIELDS_NOT_DEFINED'
    SELECTOR_FIELD_ERROR = 'SELECTOR_FIELD_ERROR'


class DauphinEvaluationStackListItemEntry(dauphin.ObjectType):
    class Meta(object):
        name = 'EvaluationStackListItemEntry'

    def __init__(self, list_index):
        super(DauphinEvaluationStackListItemEntry, self).__init__()
        self._list_index = list_index

    list_index = dauphin.NonNull(dauphin.Int)

    def resolve_list_index(self, _info):
        return self._list_index


class DauphinEvaluationStackPathEntry(dauphin.ObjectType):
    class Meta(object):
        name = 'EvaluationStackPathEntry'

    def __init__(self, field_name):
        self._field_name = check.str_param(field_name, 'field_name')
        super(DauphinEvaluationStackPathEntry, self).__init__()

    field_name = dauphin.NonNull(dauphin.String)

    def resolve_field_name(self, _info):
        return self._field_name


class DauphinEvaluationStackEntry(dauphin.Union):
    class Meta(object):
        name = 'EvaluationStackEntry'
        types = (DauphinEvaluationStackListItemEntry, DauphinEvaluationStackPathEntry)

    @staticmethod
    def from_native_entry(entry):
        if isinstance(entry, EvaluationStackPathEntry):
            return DauphinEvaluationStackPathEntry(field_name=entry.field_name)
        elif isinstance(entry, EvaluationStackListItemEntry):
            return DauphinEvaluationStackListItemEntry(list_index=entry.list_index)
        else:
            check.failed('Unsupported stack entry type {entry}'.format(entry=entry))


class DauphinEvaluationStack(dauphin.ObjectType):
    def __init__(self, config_schema_snapshot, stack):
        self._config_schema_snapshot = check.inst_param(
            config_schema_snapshot, 'config_schema_snapshot', ConfigSchemaSnapshot
        )
        self._stack = stack
        super(DauphinEvaluationStack, self).__init__()

    class Meta(object):
        name = 'EvaluationStack'

    entries = dauphin.non_null_list('EvaluationStackEntry')

    def resolve_entries(self, _):
        return map(DauphinEvaluationStackEntry.from_native_entry, self._stack.entries)


class DauphinPipelinesOrError(dauphin.Union):
    class Meta(object):
        name = 'PipelinesOrError'
        types = ('PipelineConnection', DauphinPythonError)


class DauphinExecutionPlanResult(dauphin.Union):
    class Meta(object):
        name = 'ExecutionPlanResult'
        types = (
            'ExecutionPlan',
            DauphinPipelineConfigValidationInvalid,
            DauphinPipelineNotFoundError,
            DauphinInvalidSubsetError,
            DauphinPythonError,
        )


class DauphinStartPipelineRunSuccess(dauphin.ObjectType):
    class Meta(object):
        name = 'StartPipelineRunSuccess'

    run = dauphin.Field(dauphin.NonNull('PipelineRun'))


class DauphinLaunchPipelineRunSuccess(dauphin.ObjectType):
    class Meta(object):
        name = 'LaunchPipelineRunSuccess'

    run = dauphin.Field(dauphin.NonNull('PipelineRun'))


class DauphinInvalidStepError(dauphin.ObjectType):
    class Meta(object):
        name = 'InvalidStepError'

    invalid_step_key = dauphin.NonNull(dauphin.String)


class DauphinInvalidOutputError(dauphin.ObjectType):
    class Meta(object):
        name = 'InvalidOutputError'

    step_key = dauphin.NonNull(dauphin.String)
    invalid_output_name = dauphin.NonNull(dauphin.String)


class DauphinPipelineRunConflict(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineRunConflict'
        interfaces = (DauphinError,)


pipeline_execution_error_types = (
    DauphinInvalidStepError,
    DauphinInvalidOutputError,
    DauphinPipelineConfigValidationInvalid,
    DauphinPipelineNotFoundError,
    DauphinPipelineRunConflict,
    DauphinPythonError,
)

start_pipeline_run_result_types = (
    DauphinStartPipelineRunSuccess,
    DauphinStartPipelineRunDisabledError,
)

launch_pipeline_run_result_types = (
    DauphinLaunchPipelineRunSuccess,
    DauphinRunLauncherNotDefinedError,
)


class DauphinStartPipelineExecution(dauphin.Interface):
    class Meta(object):
        name = 'DauphinStartPipelineExecution'

    message = dauphin.String(required=True)


class DauphinStartPipelineExecutionResult(dauphin.Union):
    class Meta(object):
        name = 'StartPipelineExecutionResult'
        types = start_pipeline_run_result_types + pipeline_execution_error_types


class DauphinStartPipelineExecutionForCreatedRunResult(dauphin.Union):
    class Meta(object):
        name = 'StartPipelineExecutionForCreatedRunResult'
        types = (
            start_pipeline_run_result_types
            + pipeline_execution_error_types
            + (DauphinPipelineRunNotFoundError,)
        )


class DauphinLaunchPipelineExecutionResult(dauphin.Union):
    class Meta(object):
        name = 'LaunchPipelineExecutionResult'
        types = launch_pipeline_run_result_types + pipeline_execution_error_types


class DauphinScheduledExecutionBlocked(dauphin.ObjectType):
    class Meta(object):
        name = 'ScheduledExecutionBlocked'

    message = dauphin.NonNull(dauphin.String)


class DauphinStartScheduledExecutionResult(dauphin.Union):
    class Meta(object):
        name = 'StartScheduledExecutionResult'
        types = (
            (
                DauphinScheduleNotFoundError,
                DauphinSchedulerNotDefinedError,
                DauphinScheduledExecutionBlocked,
            )
            + start_pipeline_run_result_types
            + launch_pipeline_run_result_types
            + pipeline_execution_error_types
        )


class DauphinExecutePlanSuccess(dauphin.ObjectType):
    class Meta(object):
        name = 'ExecutePlanSuccess'

    pipeline = dauphin.Field(dauphin.NonNull('Pipeline'))
    has_failures = dauphin.Field(dauphin.NonNull(dauphin.Boolean))
    step_events = dauphin.non_null_list(DauphinStepEvent)
    raw_event_records = dauphin.non_null_list(dauphin.String)


class DauphinExecutePlanResult(dauphin.Union):
    class Meta(object):
        name = 'ExecutePlanResult'
        types = (
            DauphinExecutePlanSuccess,
            DauphinPipelineConfigValidationInvalid,
            DauphinPipelineNotFoundError,
            DauphinInvalidStepError,
            DauphinPythonError,
        )


class DauphinStartPipelineReexecutionResult(dauphin.Union):
    class Meta(object):
        name = 'StartPipelineReexecutionResult'
        types = start_pipeline_run_result_types + pipeline_execution_error_types


class DauphinLaunchPipelineReexecutionResult(dauphin.Union):
    class Meta(object):
        name = 'LaunchPipelineReexecutionResult'
        types = launch_pipeline_run_result_types + pipeline_execution_error_types


class DauphinConfigTypeNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = 'ConfigTypeNotFoundError'
        interfaces = (DauphinError,)

    pipeline = dauphin.NonNull('Pipeline')
    config_type_name = dauphin.NonNull(dauphin.String)


class DauphinRuntimeTypeNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = 'RuntimeTypeNotFoundError'
        interfaces = (DauphinError,)

    runtime_type_name = dauphin.NonNull(dauphin.String)


class DauphinConfigTypeOrError(dauphin.Union):
    class Meta(object):
        name = 'ConfigTypeOrError'
        types = (
            'EnumConfigType',
            'CompositeConfigType',
            'RegularConfigType',
            DauphinPipelineNotFoundError,
            DauphinConfigTypeNotFoundError,
            DauphinPythonError,
        )


class DauphinRuntimeTypeOrError(dauphin.Union):
    class Meta(object):
        name = 'RuntimeTypeOrError'
        types = (
            'RegularRuntimeType',
            DauphinPipelineNotFoundError,
            DauphinRuntimeTypeNotFoundError,
            DauphinPythonError,
        )


class DauphinPipelineRunOrError(dauphin.Union):
    class Meta(object):
        name = 'PipelineRunOrError'
        types = ('PipelineRun', DauphinPipelineRunNotFoundError, DauphinPythonError)


class DauphinPipelineRuns(dauphin.ObjectType):
    class Meta(object):
        name = 'PipelineRuns'

    results = dauphin.non_null_list('PipelineRun')


class DauphinPipelineRunsOrError(dauphin.Union):
    class Meta(object):
        name = 'PipelineRunsOrError'
        types = (DauphinPipelineRuns, DauphinInvalidPipelineRunsFilterError, DauphinPythonError)


class DauphinRunGroupOrError(dauphin.Union):
    class Meta(object):
        name = 'RunGroupOrError'
        types = ('RunGroup', DauphinRunGroupNotFoundError, DauphinPythonError)


class DauphinPartitionSetNotFoundError(dauphin.ObjectType):
    class Meta(object):
        name = 'PartitionSetNotFoundError'
        interfaces = (DauphinError,)

    partition_set_name = dauphin.NonNull(dauphin.String)

    def __init__(self, partition_set_name):
        super(DauphinPartitionSetNotFoundError, self).__init__()
        self.partition_set_name = check.str_param(partition_set_name, 'partition_set_name')
        self.message = 'Partition set {partition_set_name} could not be found.'.format(
            partition_set_name=self.partition_set_name
        )
