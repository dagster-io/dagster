import sys
import typing

from pep562 import pep562

import dagster._module_alias_map as _module_alias_map

# Imports of a key will return the module named by the corresponding value.
sys.meta_path.insert(
    _module_alias_map.get_meta_path_insertion_index(),
    _module_alias_map.AliasedModuleFinder(
        {
            "dagster.check": "dagster._check",
        }
    ),
)

from dagster.builtins import Any, Bool, Float, Int, Nothing, String
from dagster.config import Enum, EnumValue, Field, Map, Permissive, Selector, Shape
from dagster.config.config_schema import ConfigSchema
from dagster.config.config_type import Array, Noneable, ScalarUnion
from dagster.core.asset_defs import (
    AssetGroup,
    AssetIn,
    AssetsDefinition,
    SourceAsset,
    asset,
    build_assets_job,
    multi_asset,
)
from dagster.core.definitions import (
    AssetKey,
    AssetMaterialization,
    AssetObservation,
    AssetSensorDefinition,
    BoolMetadataValue,
    CompositeSolidDefinition,
    ConfigMapping,
    DagsterAssetMetadataValue,
    DagsterPipelineRunMetadataValue,
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
    In,
    InputDefinition,
    InputMapping,
    IntMetadataValue,
    JobDefinition,
    JsonMetadataValue,
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
    StaticPartitionsDefinition,
    TableColumn,
    TableColumnConstraints,
    TableConstraints,
    TableMetadataValue,
    TableRecord,
    TableSchema,
    TableSchemaMetadataValue,
    TextMetadataValue,
    TimeWindowPartitionsDefinition,
    TypeCheck,
    UrlMetadataValue,
    WeeklyPartitionsDefinition,
    asset_sensor,
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
    logger,
    make_values_resource,
    monthly_partitioned_config,
    monthly_schedule,
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
from dagster.core.definitions.configurable import configured
from dagster.core.definitions.policy import Backoff, Jitter, RetryPolicy
from dagster.core.definitions.run_status_sensor_definition import build_run_status_sensor_context
from dagster.core.definitions.schedule_definition import build_schedule_context
from dagster.core.definitions.sensor_definition import build_sensor_context
from dagster.core.definitions.step_launcher import StepLauncher
from dagster.core.definitions.utils import (
    config_from_files,
    config_from_pkg_resources,
    config_from_yaml_strings,
)
from dagster.core.definitions.version_strategy import SourceHashVersionStrategy, VersionStrategy
from dagster.core.errors import (
    DagsterConfigMappingFunctionError,
    DagsterError,
    DagsterEventLogInvalidForRun,
    DagsterExecutionInterruptedError,
    DagsterExecutionStepExecutionError,
    DagsterExecutionStepNotFoundError,
    DagsterInvalidConfigDefinitionError,
    DagsterInvalidConfigError,
    DagsterInvalidDefinitionError,
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
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.execution.api import (
    execute_pipeline,
    execute_pipeline_iterator,
    reexecute_pipeline,
    reexecute_pipeline_iterator,
)
from dagster.core.execution.build_resources import build_resources
from dagster.core.execution.context.compute import OpExecutionContext, SolidExecutionContext
from dagster.core.execution.context.hook import HookContext, build_hook_context
from dagster.core.execution.context.init import InitResourceContext, build_init_resource_context
from dagster.core.execution.context.input import InputContext, build_input_context
from dagster.core.execution.context.invocation import build_op_context, build_solid_context
from dagster.core.execution.context.logger import InitLoggerContext
from dagster.core.execution.context.output import OutputContext, build_output_context
from dagster.core.execution.context.system import TypeCheckContext
from dagster.core.execution.execute_in_process_result import ExecuteInProcessResult
from dagster.core.execution.plan.external_step import (
    external_instance_from_step_run_ref,
    run_step_from_ref,
    step_context_to_step_run_ref,
    step_run_ref_to_step_context,
)
from dagster.core.execution.results import (
    CompositeSolidExecutionResult,
    PipelineExecutionResult,
    SolidExecutionResult,
)
from dagster.core.execution.validate_run_config import validate_run_config
from dagster.core.executor.base import Executor
from dagster.core.executor.init import InitExecutorContext
from dagster.core.instance import DagsterInstance
from dagster.core.launcher import DefaultRunLauncher
from dagster.core.log_manager import DagsterLogManager
from dagster.core.storage.event_log import (
    EventLogEntry,
    EventLogRecord,
    EventRecordsFilter,
    RunShardedEventsCursor,
)
from dagster.core.storage.file_manager import FileHandle, LocalFileHandle, local_file_manager
from dagster.core.storage.fs_asset_io_manager import fs_asset_io_manager
from dagster.core.storage.fs_io_manager import custom_path_fs_io_manager, fs_io_manager
from dagster.core.storage.io_manager import IOManager, IOManagerDefinition, io_manager
from dagster.core.storage.mem_io_manager import mem_io_manager
from dagster.core.storage.memoizable_io_manager import MemoizableIOManager
from dagster.core.storage.pipeline_run import (
    DagsterRun,
    DagsterRunStatus,
    PipelineRun,
    PipelineRunStatus,
)
from dagster.core.storage.root_input_manager import (
    RootInputManager,
    RootInputManagerDefinition,
    root_input_manager,
)
from dagster.core.storage.tags import MEMOIZED_RUN_TAG
from dagster.core.types.config_schema import (
    DagsterTypeLoader,
    DagsterTypeMaterializer,
    dagster_type_loader,
    dagster_type_materializer,
)
from dagster.core.types.dagster_type import DagsterType, List, Optional, PythonObjectDagsterType
from dagster.core.types.decorator import (
    make_python_type_usable_as_dagster_type,
    usable_as_dagster_type,
)
from dagster.core.types.python_dict import Dict
from dagster.core.types.python_set import Set
from dagster.core.types.python_tuple import Tuple
from dagster.serdes import deserialize_value, serialize_value
from dagster.utils import file_relative_path
from dagster.utils.alert import make_email_on_run_failure_sensor
from dagster.utils.backcompat import ExperimentalWarning, rename_warning
from dagster.utils.log import get_dagster_logger
from dagster.utils.partitions import (
    create_offset_partition_selector,
    date_partition_range,
    identity_partition_selector,
)
from dagster.utils.test import (
    check_dagster_type,
    execute_solid,
    execute_solid_within_pipeline,
    execute_solids_within_pipeline,
)

from .version import __version__

from dagster.config.source import BoolSource, StringSource, IntSource  # isort:skip

# ########################
# ##### DEPRECATED ALIASES
# ########################

# NOTE: Unfortunately we have to declare deprecated aliases twice-- the
# TYPE_CHECKING declaration satisfies linters and type checkers, but the entry
# in `_DEPRECATED` is required  for us to generate the deprecation warning.

if typing.TYPE_CHECKING:
    # pylint:disable=reimported
    from dagster.core.definitions import DagsterAssetMetadataValue as DagsterAssetMetadataEntryData
    from dagster.core.definitions import (
        DagsterPipelineRunMetadataValue as DagsterPipelineRunMetadataEntryData,
    )
    from dagster.core.definitions import FloatMetadataValue as FloatMetadataEntryData
    from dagster.core.definitions import IntMetadataValue as IntMetadataEntryData
    from dagster.core.definitions import JsonMetadataValue as JsonMetadataEntryData
    from dagster.core.definitions import MarkdownMetadataValue as MarkdownMetadataEntryData
    from dagster.core.definitions import MetadataEntry as EventMetadataEntry
    from dagster.core.definitions import MetadataValue as EventMetadata
    from dagster.core.definitions import PathMetadataValue as PathMetadataEntryData
    from dagster.core.definitions import (
        PythonArtifactMetadataValue as PythonArtifactMetadataEntryData,
    )
    from dagster.core.definitions import TableMetadataValue as TableMetadataEntryData
    from dagster.core.definitions import TableSchemaMetadataValue as TableSchemaMetadataEntryData
    from dagster.core.definitions import TextMetadataValue as TextMetadataEntryData
    from dagster.core.definitions import UrlMetadataValue as UrlMetadataEntryData

    # pylint:enable=reimported

_DEPRECATED = {
    "EventMetadataEntry": (MetadataEntry, "0.15.0"),
    "EventMetadata": (MetadataValue, "0.15.0"),
    "TextMetadataEntryData": (TextMetadataValue, "0.15.0"),
    "UrlMetadataEntryData": (UrlMetadataValue, "0.15.0"),
    "PathMetadataEntryData": (PathMetadataValue, "0.15.0"),
    "JsonMetadataEntryData": (JsonMetadataValue, "0.15.0"),
    "MarkdownMetadataEntryData": (MarkdownMetadataValue, "0.15.0"),
    "PythonArtifactMetadataEntryData": (
        PythonArtifactMetadataValue,
        "0.15.0",
    ),
    "FloatMetadataEntryData": (FloatMetadataValue, "0.15.0"),
    "IntMetadataEntryData": (IntMetadataValue, "0.15.0"),
    "DagsterPipelineRunMetadataEntryData": (
        DagsterPipelineRunMetadataValue,
        "0.15.0",
    ),
    "DagsterAssetMetadataEntryData": (
        DagsterAssetMetadataValue,
        "0.15.0",
    ),
    "TableMetadataEntryData": (TableMetadataValue, "0.15.0"),
    "TableSchemaMetadataEntryData": (
        TableSchemaMetadataValue,
        "0.15.0",
    ),
}


def __getattr__(name: str) -> typing.Any:
    if name in _DEPRECATED:
        value, breaking_version = _DEPRECATED[name]
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
    "AssetSensorDefinition",
    "AssetsDefinition",
    "DagsterAssetMetadataValue",
    "DagsterPipelineRunMetadataValue",
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
    "step_context_to_step_run_ref",
    "external_instance_from_step_run_ref",
    "step_run_ref_to_step_context",
    "run_step_from_ref",
    "build_init_resource_context",
    "OpExecutionContext",
    "PipelineExecutionResult",
    "RetryRequested",
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
    "TimeWindowPartitionsDefinition",
    "WeeklyPartitionsDefinition",
    "Partition",
    "PartitionedConfig",
    "PartitionsDefinition",
    "PartitionScheduleDefinition",
    "PartitionSetDefinition",
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
    "RootInputManager",
    "RootInputManagerDefinition",
    "root_input_manager",
    "fs_asset_io_manager",
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
]
