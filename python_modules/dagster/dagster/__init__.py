import importlib
import sys
import typing

from pep562 import pep562

import dagster._module_alias_map as _module_alias_map

# Imports of a key will return the module named by the corresponding value.
sys.meta_path.insert(
    _module_alias_map.get_meta_path_insertion_index(),
    _module_alias_map.AliasedModuleFinder(
        {
            "dagster.api": "dagster._api",
            "dagster.builtins": "dagster._builtins",
            "dagster.check": "dagster._check",
            "dagster.cli": "dagster._cli",
            "dagster.config": "dagster._config",
            "dagster.core": "dagster._core",
            "dagster.daemon": "dagster._daemon",
            "dagster.experimental": "dagster._experimental",
            "dagster.generate": "dagster._generate",
            "dagster.grpc": "dagster._grpc",
            "dagster.loggers": "dagster._loggers",
            "dagster.serdes": "dagster._serdes",
            "dagster.seven": "dagster._seven",
            "dagster.utils": "dagster._utils",
        }
    ),
)

from dagster._builtins import Any, Bool, Float, Int, Nothing, String
from dagster._config import (
    Array,
    BoolSource,
    ConfigSchema,
    Enum,
    EnumValue,
    Field,
    IntSource,
    Map,
    Noneable,
    Permissive,
    ScalarUnion,
    Selector,
    Shape,
    StringSource,
)
from dagster._core.definitions import (
    AllPartitionMapping,
    AssetIn,
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    AssetOut,
    AssetSelection,
    AssetSensorDefinition,
    AssetsDefinition,
    BoolMetadataValue,
    CompositeSolidDefinition,
    ConfigMapping,
    DagsterAssetMetadataValue,
    DagsterRunMetadataValue,
    DailyPartitionsDefinition,
    DefaultScheduleStatus,
    DefaultSensorStatus,
    DependencyDefinition,
    DynamicOut,
    DynamicOutput,
    DynamicOutputDefinition,
    DynamicPartitionsDefinition,
    ExecutorDefinition,
    ExecutorRequirement,
    ExpectationResult,
    Failure,
    FloatMetadataValue,
    GraphDefinition,
    GraphIn,
    GraphOut,
    HookDefinition,
    HourlyPartitionsDefinition,
    IdentityPartitionMapping,
    In,
    InputDefinition,
    InputMapping,
    IntMetadataValue,
    JobDefinition,
    JsonMetadataValue,
    LastPartitionMapping,
    LoggerDefinition,
    MarkdownMetadataValue,
    Materialization,
    MetadataEntry,
    MetadataValue,
    ModeDefinition,
    MonthlyPartitionsDefinition,
    MultiDependencyDefinition,
    NodeInvocation,
    OpDefinition,
    Out,
    Output,
    OutputDefinition,
    OutputMapping,
    Partition,
    PartitionKeyRange,
    PartitionMapping,
    PartitionScheduleDefinition,
    PartitionSetDefinition,
    PartitionedConfig,
    PartitionsDefinition,
    PathMetadataValue,
    PipelineDefinition,
    PipelineFailureSensorContext,
    PresetDefinition,
    PythonArtifactMetadataValue,
    RepositoryData,
    RepositoryDefinition,
    ResourceDefinition,
    RetryRequested,
    RunFailureSensorContext,
    RunRequest,
    RunStatusSensorContext,
    RunStatusSensorDefinition,
    ScheduleDefinition,
    ScheduleEvaluationContext,
    ScheduleExecutionContext,
    SensorDefinition,
    SensorEvaluationContext,
    SensorExecutionContext,
    SkipReason,
    SolidDefinition,
    SolidInvocation,
    SourceAsset,
    StaticPartitionsDefinition,
    TableColumn,
    TableColumnConstraints,
    TableConstraints,
    TableMetadataValue,
    TableRecord,
    TableSchema,
    TableSchemaMetadataValue,
    TextMetadataValue,
    TimeWindow,
    TimeWindowPartitionMapping,
    TimeWindowPartitionsDefinition,
    TypeCheck,
    UrlMetadataValue,
    WeeklyPartitionsDefinition,
    asset,
    asset_sensor,
    build_assets_job,
    build_init_logger_context,
    build_reconstructable_job,
    build_schedule_from_partitioned_job,
    composite_solid,
    config_mapping,
    daily_partitioned_config,
    daily_schedule,
    default_executors,
    dynamic_partitioned_config,
    executor,
    failure_hook,
    graph,
    hourly_partitioned_config,
    hourly_schedule,
    in_process_executor,
    job,
    lambda_solid,
    load_assets_from_current_module,
    load_assets_from_modules,
    load_assets_from_package_module,
    load_assets_from_package_name,
    logger,
    make_values_resource,
    materialize,
    materialize_to_memory,
    monthly_partitioned_config,
    monthly_schedule,
    multi_asset,
    multi_or_in_process_executor,
    multiple_process_executor_requirements,
    multiprocess_executor,
    op,
    pipeline,
    pipeline_failure_sensor,
    reconstructable,
    repository,
    resource,
    run_failure_sensor,
    run_status_sensor,
    schedule,
    schedule_from_partitions,
    sensor,
    solid,
    static_partitioned_config,
    success_hook,
    weekly_partitioned_config,
    weekly_schedule,
)
from dagster._core.definitions.configurable import configured
from dagster._core.definitions.policy import Backoff, Jitter, RetryPolicy
from dagster._core.definitions.run_status_sensor_definition import build_run_status_sensor_context
from dagster._core.definitions.schedule_definition import build_schedule_context
from dagster._core.definitions.sensor_definition import build_sensor_context
from dagster._core.definitions.step_launcher import StepLauncher
from dagster._core.definitions.unresolved_asset_job_definition import define_asset_job
from dagster._core.definitions.utils import (
    config_from_files,
    config_from_pkg_resources,
    config_from_yaml_strings,
)
from dagster._core.definitions.version_strategy import SourceHashVersionStrategy, VersionStrategy
from dagster._core.errors import (
    DagsterConfigMappingFunctionError,
    DagsterError,
    DagsterEventLogInvalidForRun,
    DagsterExecutionInterruptedError,
    DagsterExecutionStepExecutionError,
    DagsterExecutionStepNotFoundError,
    DagsterInvalidConfigDefinitionError,
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError,
    DagsterInvariantViolationError,
    DagsterResourceFunctionError,
    DagsterRunNotFoundError,
    DagsterStepOutputNotFoundError,
    DagsterSubprocessError,
    DagsterTypeCheckDidNotPass,
    DagsterTypeCheckError,
    DagsterUnknownPartitionError,
    DagsterUnknownResourceError,
    DagsterUnmetExecutorRequirementsError,
    DagsterUserCodeExecutionError,
    raise_execution_interrupts,
)
from dagster._core.events import DagsterEvent, DagsterEventType
from dagster._core.execution.api import (
    ReexecutionOptions,
    execute_job,
    execute_pipeline,
    execute_pipeline_iterator,
    reexecute_pipeline,
    reexecute_pipeline_iterator,
)
from dagster._core.execution.build_resources import build_resources
from dagster._core.execution.context.compute import OpExecutionContext, SolidExecutionContext
from dagster._core.execution.context.hook import HookContext, build_hook_context
from dagster._core.execution.context.init import InitResourceContext, build_init_resource_context
from dagster._core.execution.context.input import InputContext, build_input_context
from dagster._core.execution.context.invocation import build_op_context, build_solid_context
from dagster._core.execution.context.logger import InitLoggerContext
from dagster._core.execution.context.output import OutputContext, build_output_context
from dagster._core.execution.context.system import TypeCheckContext
from dagster._core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster._core.execution.execute_job_result import ExecuteJobResult
from dagster._core.execution.plan.external_step import (
    external_instance_from_step_run_ref,
    run_step_from_ref,
    step_context_to_step_run_ref,
    step_run_ref_to_step_context,
)
from dagster._core.execution.results import (
    CompositeSolidExecutionResult,
    PipelineExecutionResult,
    SolidExecutionResult,
)
from dagster._core.execution.validate_run_config import validate_run_config
from dagster._core.execution.with_resources import with_resources
from dagster._core.executor.base import Executor
from dagster._core.executor.init import InitExecutorContext
from dagster._core.instance import DagsterInstance
from dagster._core.launcher import DefaultRunLauncher
from dagster._core.log_manager import DagsterLogManager
from dagster._core.storage.event_log import (
    EventLogEntry,
    EventLogRecord,
    EventRecordsFilter,
    RunShardedEventsCursor,
)
from dagster._core.storage.file_manager import FileHandle, LocalFileHandle, local_file_manager
from dagster._core.storage.fs_io_manager import custom_path_fs_io_manager, fs_io_manager
from dagster._core.storage.input_manager import InputManager, input_manager
from dagster._core.storage.io_manager import IOManager, IOManagerDefinition, io_manager
from dagster._core.storage.mem_io_manager import mem_io_manager
from dagster._core.storage.memoizable_io_manager import MemoizableIOManager
from dagster._core.storage.pipeline_run import (
    DagsterRun,
    DagsterRunStatus,
    PipelineRun,
    PipelineRunStatus,
)
from dagster._core.storage.root_input_manager import (
    RootInputManager,
    RootInputManagerDefinition,
    root_input_manager,
)
from dagster._core.storage.tags import MEMOIZED_RUN_TAG
from dagster._core.types.config_schema import (
    DagsterTypeLoader,
    DagsterTypeMaterializer,
    dagster_type_loader,
    dagster_type_materializer,
)
from dagster._core.types.dagster_type import DagsterType, List, Optional, PythonObjectDagsterType
from dagster._core.types.decorator import (
    make_python_type_usable_as_dagster_type,
    usable_as_dagster_type,
)
from dagster._core.types.python_dict import Dict
from dagster._core.types.python_set import Set
from dagster._core.types.python_tuple import Tuple
from dagster._serdes import deserialize_value, serialize_value

from .version import __version__

# isort: split
from dagster._loggers import (
    colored_console_logger,
    default_loggers,
    default_system_loggers,
    json_console_logger,
)
from dagster._utils import file_relative_path
from dagster._utils.alert import make_email_on_run_failure_sensor
from dagster._utils.backcompat import ExperimentalWarning, deprecation_warning, rename_warning
from dagster._utils.log import get_dagster_logger
from dagster._utils.partitions import (
    create_offset_partition_selector,
    date_partition_range,
    identity_partition_selector,
)
from dagster._utils.test import (
    check_dagster_type,
    execute_solid,
    execute_solid_within_pipeline,
    execute_solids_within_pipeline,
)

# ########################
# ##### DEPRECATED ALIASES
# ########################

# NOTE: Unfortunately we have to declare deprecated aliases twice-- the
# TYPE_CHECKING declaration satisfies linters and type checkers, but the entry
# in `_DEPRECATED` is required  for us to generate the deprecation warning.

if typing.TYPE_CHECKING:
    # pylint:disable=reimported
    from dagster._core.definitions import AssetGroup
    from dagster._core.definitions import DagsterAssetMetadataValue as DagsterAssetMetadataEntryData
    from dagster._core.definitions import (
        DagsterRunMetadataValue as DagsterPipelineRunMetadataEntryData,
    )
    from dagster._core.definitions import DagsterRunMetadataValue as DagsterPipelineRunMetadataValue
    from dagster._core.definitions import FloatMetadataValue as FloatMetadataEntryData
    from dagster._core.definitions import IntMetadataValue as IntMetadataEntryData
    from dagster._core.definitions import JsonMetadataValue as JsonMetadataEntryData
    from dagster._core.definitions import MarkdownMetadataValue as MarkdownMetadataEntryData
    from dagster._core.definitions import MetadataEntry as EventMetadataEntry
    from dagster._core.definitions import MetadataValue as EventMetadata
    from dagster._core.definitions import PathMetadataValue as PathMetadataEntryData
    from dagster._core.definitions import (
        PythonArtifactMetadataValue as PythonArtifactMetadataEntryData,
    )
    from dagster._core.definitions import TableMetadataValue as TableMetadataEntryData
    from dagster._core.definitions import TableSchemaMetadataValue as TableSchemaMetadataEntryData
    from dagster._core.definitions import TextMetadataValue as TextMetadataEntryData
    from dagster._core.definitions import UrlMetadataValue as UrlMetadataEntryData

    # pylint:enable=reimported

_DEPRECATED = {
    "AssetGroup": (
        "dagster._core.definitions",
        "1.0.0",
        "Instead, place a set of assets wrapped with `with_resources` directly on a repository.",
    ),
}

_DEPRECATED_RENAMED = {
    "EventMetadataEntry": (MetadataEntry, "1.0.0"),
    "EventMetadata": (MetadataValue, "1.0.0"),
    "TextMetadataEntryData": (TextMetadataValue, "1.0.0"),
    "UrlMetadataEntryData": (UrlMetadataValue, "1.0.0"),
    "PathMetadataEntryData": (PathMetadataValue, "1.0.0"),
    "JsonMetadataEntryData": (JsonMetadataValue, "1.0.0"),
    "MarkdownMetadataEntryData": (MarkdownMetadataValue, "1.0.0"),
    "PythonArtifactMetadataEntryData": (
        PythonArtifactMetadataValue,
        "1.0.0",
    ),
    "FloatMetadataEntryData": (FloatMetadataValue, "1.0.0"),
    "IntMetadataEntryData": (IntMetadataValue, "1.0.0"),
    "DagsterPipelineRunMetadataEntryData": (
        DagsterRunMetadataValue,
        "1.0.0",
    ),
    "DagsterAssetMetadataEntryData": (
        DagsterAssetMetadataValue,
        "1.0.0",
    ),
    "TableMetadataEntryData": (TableMetadataValue, "1.0.0"),
    "TableSchemaMetadataEntryData": (
        TableSchemaMetadataValue,
        "1.0.0",
    ),
    "DagsterPipelineRunMetadataValue": (DagsterRunMetadataValue, "1.0.0"),
}


def __getattr__(name: str) -> typing.Any:
    if name in _DEPRECATED:
        module, breaking_version, additional_warn_text = _DEPRECATED[name]
        value = getattr(importlib.import_module(module), name)
        stacklevel = 3 if sys.version_info >= (3, 7) else 4
        deprecation_warning(name, breaking_version, additional_warn_text, stacklevel=stacklevel)
        return value
    elif name in _DEPRECATED_RENAMED:
        value, breaking_version = _DEPRECATED_RENAMED[name]
        stacklevel = 3 if sys.version_info >= (3, 7) else 4
        rename_warning(value.__name__, name, breaking_version, stacklevel=stacklevel)
        return value
    else:
        raise AttributeError("module '{}' has no attribute '{}'".format(__name__, name))


def __dir__() -> typing.List[str]:
    return sorted(list(__all__) + list(_DEPRECATED.keys()))


# Backports PEP 562, which allows for override of __getattr__ and __dir__, to this module. PEP 562
# was introduced in Python 3.7, so the `pep562` call here is a no-op for 3.7+.
# See:
#  PEP 562: https://www.python.org/dev/peps/pep-0562/
#  PEP 562 backport package: https://github.com/facelessuser/pep562
pep562(__name__)

__all__ = [
    # Definition
    "AssetGroup",
    "AssetKey",
    "AssetIn",
    "AssetMaterialization",
    "AssetObservation",
    "AssetOut",
    "AssetSelection",
    "AssetSensorDefinition",
    "AssetsDefinition",
    "DagsterAssetMetadataValue",
    "DagsterRunMetadataValue",
    "TableColumn",
    "TableColumnConstraints",
    "TableConstraints",
    "TableRecord",
    "TableSchemaMetadataValue",
    "TableSchema",
    "CompositeSolidDefinition",
    "ConfigMapping",
    "DependencyDefinition",
    "MetadataValue",
    "MetadataEntry",
    "ExecutorDefinition",
    "ExecutorRequirement",
    "ExpectationResult",
    "Failure",
    "Field",
    "Map",
    "GraphDefinition",
    "GraphIn",
    "GraphOut",
    "HookDefinition",
    "JobDefinition",
    "In",
    "InputDefinition",
    "InputMapping",
    "JsonMetadataValue",
    "LoggerDefinition",
    "build_init_logger_context",
    "BoolMetadataValue",
    "MarkdownMetadataValue",
    "IntMetadataValue",
    "FloatMetadataValue",
    "Materialization",
    "ModeDefinition",
    "MultiDependencyDefinition",
    "OpDefinition",
    "Out",
    "Output",
    "OutputDefinition",
    "OutputMapping",
    "PathMetadataValue",
    "PipelineDefinition",
    "PresetDefinition",
    "PythonArtifactMetadataValue",
    "RepositoryData",
    "RepositoryDefinition",
    "ResourceDefinition",
    "SolidDefinition",
    "SourceAsset",
    "NodeInvocation",
    "SolidInvocation",
    "TableMetadataValue",
    "TextMetadataValue",
    "UrlMetadataValue",
    "make_values_resource",
    "RetryPolicy",
    "Backoff",
    "Jitter",
    "RunStatusSensorDefinition",
    "DynamicOutput",
    "DynamicOut",
    "DynamicOutputDefinition",
    # Decorators
    "asset",
    "asset_sensor",
    "composite_solid",
    "config_mapping",
    "executor",
    "graph",
    "job",
    "lambda_solid",
    "logger",
    "multi_asset",
    "multi_or_in_process_executor",
    "op",
    "pipeline",
    "repository",
    "resource",
    "schedule",
    "sensor",
    "solid",
    "success_hook",
    "failure_hook",
    "run_failure_sensor",
    "pipeline_failure_sensor",
    "run_status_sensor",
    # Execution
    "CompositeSolidExecutionResult",
    "DagsterEvent",
    "DagsterEventType",
    "DefaultRunLauncher",
    "EventLogEntry",
    "EventLogRecord",
    "Executor",
    "InitExecutorContext",
    "InitLoggerContext",
    "InitResourceContext",
    "ExecuteInProcessResult",
    "ExecuteJobResult",
    "step_context_to_step_run_ref",
    "external_instance_from_step_run_ref",
    "step_run_ref_to_step_context",
    "run_step_from_ref",
    "build_init_resource_context",
    "OpExecutionContext",
    "PipelineExecutionResult",
    "RetryRequested",
    "with_resources",
    "build_resources",
    "SolidExecutionResult",
    "SolidExecutionContext",
    "build_solid_context",
    "build_op_context",
    "HookContext",
    "build_hook_context",
    "TypeCheckContext",
    "InputContext",
    "build_input_context",
    "OutputContext",
    "build_output_context",
    "PipelineRun",
    "DagsterRun",
    "PipelineRunStatus",
    "DagsterRunStatus",
    "default_executors",
    "execute_pipeline_iterator",
    "execute_pipeline",
    "execute_job",
    "ReexecutionOptions",
    "validate_run_config",
    "execute_solid_within_pipeline",
    "in_process_executor",
    "multiprocess_executor",
    "multiple_process_executor_requirements",
    "build_reconstructable_job",
    "reconstructable",
    "reexecute_pipeline_iterator",
    "reexecute_pipeline",
    # Errors
    "DagsterConfigMappingFunctionError",
    "DagsterError",
    "DagsterEventLogInvalidForRun",
    "DagsterExecutionInterruptedError",
    "DagsterExecutionStepExecutionError",
    "DagsterExecutionStepNotFoundError",
    "DagsterInvalidConfigDefinitionError",
    "DagsterInvalidInvocationError",
    "DagsterInvalidConfigError",
    "DagsterInvalidDefinitionError",
    "DagsterInvariantViolationError",
    "DagsterResourceFunctionError",
    "DagsterRunNotFoundError",
    "DagsterStepOutputNotFoundError",
    "DagsterSubprocessError",
    "DagsterTypeCheckDidNotPass",
    "DagsterTypeCheckError",
    "DagsterUnknownPartitionError",
    "DagsterUnknownResourceError",
    "DagsterUnmetExecutorRequirementsError",
    "DagsterUserCodeExecutionError",
    "raise_execution_interrupts",
    # Logging
    "DagsterLogManager",
    "get_dagster_logger",
    # Utilities
    "check_dagster_type",
    "execute_solid",
    "execute_solids_within_pipeline",
    "file_relative_path",
    "config_from_files",
    "config_from_pkg_resources",
    "config_from_yaml_strings",
    "configured",
    "build_assets_job",
    "define_asset_job",
    "load_assets_from_modules",
    "load_assets_from_current_module",
    "load_assets_from_package_module",
    "load_assets_from_package_name",
    "materialize",
    "materialize_to_memory",
    # types
    "Any",
    "Bool",
    "Dict",
    "Enum",
    "EnumValue",
    "Float",
    "Int",
    "List",
    "Nothing",
    "Optional",
    "Set",
    "String",
    "Tuple",
    "TypeCheck",
    "dagster_type_loader",
    "DagsterTypeLoader",
    "dagster_type_materializer",
    "DagsterTypeMaterializer",
    # type creation
    "DagsterType",
    "PythonObjectDagsterType",
    "make_python_type_usable_as_dagster_type",
    "usable_as_dagster_type",
    # config
    "Array",
    "BoolSource",
    "ConfigSchema",
    "Noneable",
    "Permissive",
    "ScalarUnion",
    "StringSource",
    "IntSource",
    "Selector",
    "Shape",
    # file things
    "FileHandle",
    "LocalFileHandle",
    "local_file_manager",
    # instance
    "DagsterInstance",
    # storage
    "EventRecordsFilter",
    "RunShardedEventsCursor",
    "serialize_value",
    "deserialize_value",
    # partitions and schedules
    "build_schedule_from_partitioned_job",
    "schedule_from_partitions",
    "dynamic_partitioned_config",
    "static_partitioned_config",
    "daily_partitioned_config",
    "hourly_partitioned_config",
    "monthly_partitioned_config",
    "weekly_partitioned_config",
    "DynamicPartitionsDefinition",
    "StaticPartitionsDefinition",
    "DailyPartitionsDefinition",
    "HourlyPartitionsDefinition",
    "MonthlyPartitionsDefinition",
    "PartitionKeyRange",
    "TimeWindow",
    "TimeWindowPartitionsDefinition",
    "WeeklyPartitionsDefinition",
    "Partition",
    "PartitionedConfig",
    "PartitionsDefinition",
    "PartitionScheduleDefinition",
    "PartitionSetDefinition",
    "PartitionMapping",
    "IdentityPartitionMapping",
    "LastPartitionMapping",
    "AllPartitionMapping",
    "TimeWindowPartitionMapping",
    "RunRequest",
    "ScheduleDefinition",
    "ScheduleEvaluationContext",
    "ScheduleExecutionContext",
    "DefaultScheduleStatus",
    "build_schedule_context",
    "SensorDefinition",
    "SensorEvaluationContext",
    "SensorExecutionContext",
    "DefaultSensorStatus",
    "RunFailureSensorContext",
    "PipelineFailureSensorContext",
    "RunStatusSensorContext",
    "build_sensor_context",
    "build_run_status_sensor_context",
    "StepLauncher",
    "SkipReason",
    "daily_schedule",
    "hourly_schedule",
    "monthly_schedule",
    "weekly_schedule",
    "create_offset_partition_selector",
    "date_partition_range",
    "identity_partition_selector",
    "make_email_on_run_failure_sensor",
    # IO managers
    "IOManager",
    "IOManagerDefinition",
    "io_manager",
    "input_manager",
    "InputManager",
    "RootInputManager",
    "RootInputManagerDefinition",
    "root_input_manager",
    "fs_io_manager",
    "mem_io_manager",
    "custom_path_fs_io_manager",
    # warnings
    "ExperimentalWarning",
    # Versioning / Memoization
    "VersionStrategy",
    "MEMOIZED_RUN_TAG",
    "MemoizableIOManager",
    "SourceHashVersionStrategy",
    "colored_console_logger",
    "default_loggers",
    "default_system_loggers",
    "json_console_logger",
]
