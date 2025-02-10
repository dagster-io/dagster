import sys

from dagster import _module_alias_map

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
            "dagster.time": "dagster._time",
            "dagster.utils": "dagster._utils",
            # Added in 1.3.4 for backcompat when `_core.storage.pipeline_run` was renamed to
            # `_core.storage.dagster_run`. This was necessary because some docs (incorrectly)
            # demonstarted a direct import from `dagster._core.storage.pipeline_run` instead of
            # using the top-level import.
            "dagster._core.storage.pipeline_run": "dagster.core.storage.dagster_run",
        }
    ),
)

# ########################
# ##### NOTES ON IMPORT FORMAT
# ########################
#
# This file defines dagster's public API. Imports need to be structured/formatted so as to to ensure
# that the broadest possible set of static analyzers understand Dagster's public API as intended.
# The below guidelines ensure this is the case.
#
# (1) All imports in this module intended to define exported symbols should be of the form `from
# dagster.foo import X as X`. This is because imported symbols are not by default considered public
# by static analyzers. The redundant alias form `import X as X` overwrites the private imported `X`
# with a public `X` bound to the same value. It is also possible to expose `X` as public by listing
# it inside `__all__`, but the redundant alias form is preferred here due to easier maintainability.

# (2) All imports should target the module in which a symbol is actually defined, rather than a
# container module where it is imported. This rule also derives from the default private status of
# imported symbols. So long as there is a private import somewhere in the import chain leading from
# an import to its definition, some linters will be triggered (e.g. pyright). For example, the
# following results in a linter error when using dagster as a third-party library:

#     ### dagster/foo/bar.py
#     BAR = "BAR"
#
#     ### dagster/foo/__init__.py
#     from .bar import BAR  # BAR is imported so it is not part of dagster.foo public interface
#     FOO = "FOO"
#
#     ### dagster/__init__.py
#     from .foo import FOO, BAR  # importing BAR is importing a private symbol from dagster.foo
#     __all__ = ["FOO", "BAR"]
#
#     ### some_user_code.py
#     # from dagster import BAR  # linter error even though `BAR` is in `dagster.__all__`!
#
# We could get around this by always remembering to use the `from .foo import X as X` form in
# containers, but it is simpler to just import directly from the defining module.

# ########################
# ##### DYNAMIC IMPORTS
# ########################

from dagster._builtins import (
    Any as Any,
    Bool as Bool,
    Float as Float,
    Int as Int,
    Nothing as Nothing,
    String as String,
)
from dagster._config.config_schema import ConfigSchema as ConfigSchema
from dagster._config.config_type import (
    Array as Array,
    Enum as Enum,
    EnumValue as EnumValue,
    Noneable as Noneable,
    ScalarUnion as ScalarUnion,
)
from dagster._config.field import Field as Field
from dagster._config.field_utils import (
    EnvVar as EnvVar,
    Map as Map,
    Permissive as Permissive,
    Selector as Selector,
    Shape as Shape,
)
from dagster._config.pythonic_config import (
    Config as Config,
    ConfigurableIOManager as ConfigurableIOManager,
    ConfigurableIOManagerFactory as ConfigurableIOManagerFactory,
    ConfigurableLegacyIOManagerAdapter as ConfigurableLegacyIOManagerAdapter,
    ConfigurableResource as ConfigurableResource,
    IAttachDifferentObjectToOpContext as IAttachDifferentObjectToOpContext,
    PermissiveConfig as PermissiveConfig,
    ResourceDependency as ResourceDependency,
)
from dagster._config.source import (
    BoolSource as BoolSource,
    IntSource as IntSource,
    StringSource as StringSource,
)
from dagster._core.definitions import AssetCheckResult as AssetCheckResult
from dagster._core.definitions.asset_check_factories.freshness_checks.last_update import (
    build_last_update_freshness_checks as build_last_update_freshness_checks,
)
from dagster._core.definitions.asset_check_factories.freshness_checks.sensor import (
    build_sensor_for_freshness_checks as build_sensor_for_freshness_checks,
)
from dagster._core.definitions.asset_check_factories.freshness_checks.time_partition import (
    build_time_partition_freshness_checks as build_time_partition_freshness_checks,
)
from dagster._core.definitions.asset_check_factories.metadata_bounds_checks import (
    build_metadata_bounds_checks as build_metadata_bounds_checks,
)
from dagster._core.definitions.asset_check_factories.schema_change_checks import (
    build_column_schema_change_checks as build_column_schema_change_checks,
)
from dagster._core.definitions.asset_check_spec import (
    AssetCheckKey as AssetCheckKey,
    AssetCheckSeverity as AssetCheckSeverity,
    AssetCheckSpec as AssetCheckSpec,
)
from dagster._core.definitions.asset_checks import AssetChecksDefinition as AssetChecksDefinition
from dagster._core.definitions.asset_dep import AssetDep as AssetDep
from dagster._core.definitions.asset_in import AssetIn as AssetIn
from dagster._core.definitions.asset_out import AssetOut as AssetOut
from dagster._core.definitions.asset_selection import AssetSelection as AssetSelection
from dagster._core.definitions.asset_sensor_definition import (
    AssetSensorDefinition as AssetSensorDefinition,
)
from dagster._core.definitions.asset_spec import (
    AssetSpec as AssetSpec,
    map_asset_specs as map_asset_specs,
)
from dagster._core.definitions.assets import AssetsDefinition as AssetsDefinition
from dagster._core.definitions.auto_materialize_policy import (
    AutoMaterializePolicy as AutoMaterializePolicy,
)
from dagster._core.definitions.auto_materialize_rule import (
    AutoMaterializeRule as AutoMaterializeRule,
)
from dagster._core.definitions.auto_materialize_rule_impls import (
    AutoMaterializeAssetPartitionsFilter as AutoMaterializeAssetPartitionsFilter,
)
from dagster._core.definitions.automation_condition_sensor_definition import (
    AutomationConditionSensorDefinition as AutomationConditionSensorDefinition,
)
from dagster._core.definitions.backfill_policy import BackfillPolicy as BackfillPolicy
from dagster._core.definitions.composition import PendingNodeInvocation as PendingNodeInvocation
from dagster._core.definitions.config import ConfigMapping as ConfigMapping
from dagster._core.definitions.configurable import configured as configured
from dagster._core.definitions.data_version import (
    DataProvenance as DataProvenance,
    DataVersion as DataVersion,
    DataVersionsByPartition as DataVersionsByPartition,
)
from dagster._core.definitions.declarative_automation.automation_condition import (
    AutomationCondition as AutomationCondition,
    AutomationResult as AutomationResult,
)
from dagster._core.definitions.declarative_automation.automation_condition_tester import (
    evaluate_automation_conditions as evaluate_automation_conditions,
)
from dagster._core.definitions.declarative_automation.automation_context import (
    AutomationContext as AutomationContext,
)
from dagster._core.definitions.decorators.asset_check_decorator import (
    asset_check as asset_check,
    multi_asset_check as multi_asset_check,
)
from dagster._core.definitions.decorators.asset_decorator import (
    asset as asset,
    graph_asset as graph_asset,
    graph_multi_asset as graph_multi_asset,
    multi_asset as multi_asset,
)
from dagster._core.definitions.decorators.config_mapping_decorator import (
    config_mapping as config_mapping,
)
from dagster._core.definitions.decorators.graph_decorator import graph as graph
from dagster._core.definitions.decorators.hook_decorator import (
    failure_hook as failure_hook,
    success_hook as success_hook,
)
from dagster._core.definitions.decorators.job_decorator import job as job
from dagster._core.definitions.decorators.op_decorator import op as op
from dagster._core.definitions.decorators.repository_decorator import repository as repository
from dagster._core.definitions.decorators.schedule_decorator import schedule as schedule
from dagster._core.definitions.decorators.sensor_decorator import (
    asset_sensor as asset_sensor,
    multi_asset_sensor as multi_asset_sensor,
    sensor as sensor,
)
from dagster._core.definitions.decorators.source_asset_decorator import (
    multi_observable_source_asset as multi_observable_source_asset,
    observable_source_asset as observable_source_asset,
)
from dagster._core.definitions.definitions_class import (
    BindResourcesToJobs as BindResourcesToJobs,
    Definitions as Definitions,
    create_repository_using_definitions_args as create_repository_using_definitions_args,
)
from dagster._core.definitions.dependency import (
    DependencyDefinition as DependencyDefinition,
    MultiDependencyDefinition as MultiDependencyDefinition,
    NodeInvocation as NodeInvocation,
)
from dagster._core.definitions.dynamic_partitions_request import (
    AddDynamicPartitionsRequest as AddDynamicPartitionsRequest,
    DeleteDynamicPartitionsRequest as DeleteDynamicPartitionsRequest,
)
from dagster._core.definitions.events import (
    AssetKey as AssetKey,
    AssetMaterialization as AssetMaterialization,
    AssetObservation as AssetObservation,
    DynamicOutput as DynamicOutput,
    ExpectationResult as ExpectationResult,
    Failure as Failure,
    Output as Output,
    RetryRequested as RetryRequested,
    TypeCheck as TypeCheck,
)
from dagster._core.definitions.executor_definition import (
    ExecutorDefinition as ExecutorDefinition,
    ExecutorRequirement as ExecutorRequirement,
    executor as executor,
    in_process_executor as in_process_executor,
    multi_or_in_process_executor as multi_or_in_process_executor,
    multiple_process_executor_requirements as multiple_process_executor_requirements,
    multiprocess_executor as multiprocess_executor,
)
from dagster._core.definitions.freshness_policy import FreshnessPolicy as FreshnessPolicy
from dagster._core.definitions.graph_definition import GraphDefinition as GraphDefinition
from dagster._core.definitions.hook_definition import HookDefinition as HookDefinition
from dagster._core.definitions.input import (
    GraphIn as GraphIn,
    In as In,
    InputMapping as InputMapping,
)
from dagster._core.definitions.job_definition import JobDefinition as JobDefinition
from dagster._core.definitions.logger_definition import (
    LoggerDefinition as LoggerDefinition,
    build_init_logger_context as build_init_logger_context,
    logger as logger,
)
from dagster._core.definitions.materialize import (
    materialize as materialize,
    materialize_to_memory as materialize_to_memory,
)
from dagster._core.definitions.metadata import (
    AnchorBasedFilePathMapping as AnchorBasedFilePathMapping,
    BoolMetadataValue as BoolMetadataValue,
    CodeReferencesMetadataValue as CodeReferencesMetadataValue,
    DagsterAssetMetadataValue as DagsterAssetMetadataValue,
    DagsterJobMetadataValue as DagsterJobMetadataValue,
    DagsterRunMetadataValue as DagsterRunMetadataValue,
    FilePathMapping as FilePathMapping,
    FloatMetadataValue as FloatMetadataValue,
    IntMetadataValue as IntMetadataValue,
    JsonMetadataValue as JsonMetadataValue,
    LocalFileCodeReference as LocalFileCodeReference,
    MarkdownMetadataValue as MarkdownMetadataValue,
    MetadataEntry as MetadataEntry,
    MetadataValue as MetadataValue,
    NotebookMetadataValue as NotebookMetadataValue,
    NullMetadataValue as NullMetadataValue,
    PathMetadataValue as PathMetadataValue,
    PythonArtifactMetadataValue as PythonArtifactMetadataValue,
    TableColumnLineageMetadataValue as TableColumnLineageMetadataValue,
    TableMetadataValue as TableMetadataValue,
    TableSchemaMetadataValue as TableSchemaMetadataValue,
    TextMetadataValue as TextMetadataValue,
    TimestampMetadataValue as TimestampMetadataValue,
    UrlCodeReference as UrlCodeReference,
    UrlMetadataValue as UrlMetadataValue,
    link_code_references_to_git as link_code_references_to_git,
    with_source_code_references as with_source_code_references,
)
from dagster._core.definitions.metadata.table import (
    TableColumn as TableColumn,
    TableColumnConstraints as TableColumnConstraints,
    TableColumnDep as TableColumnDep,
    TableColumnLineage as TableColumnLineage,
    TableConstraints as TableConstraints,
    TableRecord as TableRecord,
    TableSchema as TableSchema,
)
from dagster._core.definitions.module_loaders.load_asset_checks_from_modules import (
    load_asset_checks_from_current_module as load_asset_checks_from_current_module,
    load_asset_checks_from_modules as load_asset_checks_from_modules,
    load_asset_checks_from_package_module as load_asset_checks_from_package_module,
    load_asset_checks_from_package_name as load_asset_checks_from_package_name,
)
from dagster._core.definitions.module_loaders.load_assets_from_modules import (
    load_assets_from_current_module as load_assets_from_current_module,
    load_assets_from_modules as load_assets_from_modules,
    load_assets_from_package_module as load_assets_from_package_module,
    load_assets_from_package_name as load_assets_from_package_name,
)
from dagster._core.definitions.module_loaders.load_defs_from_module import (
    load_definitions_from_current_module as load_definitions_from_current_module,
    load_definitions_from_module as load_definitions_from_module,
    load_definitions_from_modules as load_definitions_from_modules,
    load_definitions_from_package_module as load_definitions_from_package_module,
    load_definitions_from_package_name as load_definitions_from_package_name,
)
from dagster._core.definitions.multi_asset_sensor_definition import (
    MultiAssetSensorDefinition as MultiAssetSensorDefinition,
    MultiAssetSensorEvaluationContext as MultiAssetSensorEvaluationContext,
    build_multi_asset_sensor_context as build_multi_asset_sensor_context,
)
from dagster._core.definitions.multi_dimensional_partitions import (
    MultiPartitionKey as MultiPartitionKey,
    MultiPartitionsDefinition as MultiPartitionsDefinition,
)
from dagster._core.definitions.op_definition import OpDefinition as OpDefinition
from dagster._core.definitions.output import (
    DynamicOut as DynamicOut,
    GraphOut as GraphOut,
    Out as Out,
    OutputMapping as OutputMapping,
)
from dagster._core.definitions.partition import (
    DynamicPartitionsDefinition as DynamicPartitionsDefinition,
    Partition as Partition,
    PartitionedConfig as PartitionedConfig,
    PartitionsDefinition as PartitionsDefinition,
    StaticPartitionsDefinition as StaticPartitionsDefinition,
    dynamic_partitioned_config as dynamic_partitioned_config,
    partitioned_config as partitioned_config,
    static_partitioned_config as static_partitioned_config,
)
from dagster._core.definitions.partition_key_range import PartitionKeyRange as PartitionKeyRange
from dagster._core.definitions.partition_mapping import (
    AllPartitionMapping as AllPartitionMapping,
    DimensionPartitionMapping as DimensionPartitionMapping,
    IdentityPartitionMapping as IdentityPartitionMapping,
    LastPartitionMapping as LastPartitionMapping,
    MultiPartitionMapping as MultiPartitionMapping,
    MultiToSingleDimensionPartitionMapping as MultiToSingleDimensionPartitionMapping,
    PartitionMapping as PartitionMapping,
    SpecificPartitionsPartitionMapping as SpecificPartitionsPartitionMapping,
    StaticPartitionMapping as StaticPartitionMapping,
)
from dagster._core.definitions.partitioned_schedule import (
    build_schedule_from_partitioned_job as build_schedule_from_partitioned_job,
)
from dagster._core.definitions.policy import (
    Backoff as Backoff,
    Jitter as Jitter,
    RetryPolicy as RetryPolicy,
)
from dagster._core.definitions.reconstruct import (
    build_reconstructable_job as build_reconstructable_job,
    reconstructable as reconstructable,
)
from dagster._core.definitions.repository_definition import (
    RepositoryData as RepositoryData,
    RepositoryDefinition as RepositoryDefinition,
)
from dagster._core.definitions.resource_annotation import ResourceParam as ResourceParam
from dagster._core.definitions.resource_definition import (
    ResourceDefinition as ResourceDefinition,
    make_values_resource as make_values_resource,
    resource as resource,
)
from dagster._core.definitions.result import (
    MaterializeResult as MaterializeResult,
    ObserveResult as ObserveResult,
)
from dagster._core.definitions.run_config import RunConfig as RunConfig
from dagster._core.definitions.run_request import (
    RunRequest as RunRequest,
    SensorResult as SensorResult,
    SkipReason as SkipReason,
)
from dagster._core.definitions.run_status_sensor_definition import (
    RunFailureSensorContext as RunFailureSensorContext,
    RunStatusSensorContext as RunStatusSensorContext,
    RunStatusSensorDefinition as RunStatusSensorDefinition,
    build_run_status_sensor_context as build_run_status_sensor_context,
    run_failure_sensor as run_failure_sensor,
    run_status_sensor as run_status_sensor,
)
from dagster._core.definitions.schedule_definition import (
    DefaultScheduleStatus as DefaultScheduleStatus,
    ScheduleDefinition as ScheduleDefinition,
    ScheduleEvaluationContext as ScheduleEvaluationContext,
    build_schedule_context as build_schedule_context,
)
from dagster._core.definitions.selector import (
    CodeLocationSelector as CodeLocationSelector,
    JobSelector as JobSelector,
    RepositorySelector as RepositorySelector,
)
from dagster._core.definitions.sensor_definition import (
    DefaultSensorStatus as DefaultSensorStatus,
    SensorDefinition as SensorDefinition,
    SensorEvaluationContext as SensorEvaluationContext,
    SensorReturnTypesUnion as SensorReturnTypesUnion,
    build_sensor_context as build_sensor_context,
)
from dagster._core.definitions.source_asset import SourceAsset as SourceAsset
from dagster._core.definitions.step_launcher import (
    StepLauncher as StepLauncher,
    StepRunRef as StepRunRef,
)
from dagster._core.definitions.time_window_partition_mapping import (
    TimeWindowPartitionMapping as TimeWindowPartitionMapping,
)
from dagster._core.definitions.time_window_partitions import (
    DailyPartitionsDefinition as DailyPartitionsDefinition,
    HourlyPartitionsDefinition as HourlyPartitionsDefinition,
    MonthlyPartitionsDefinition as MonthlyPartitionsDefinition,
    TimeWindow as TimeWindow,
    TimeWindowPartitionsDefinition as TimeWindowPartitionsDefinition,
    WeeklyPartitionsDefinition as WeeklyPartitionsDefinition,
    daily_partitioned_config as daily_partitioned_config,
    hourly_partitioned_config as hourly_partitioned_config,
    monthly_partitioned_config as monthly_partitioned_config,
    weekly_partitioned_config as weekly_partitioned_config,
)
from dagster._core.definitions.unresolved_asset_job_definition import (
    define_asset_job as define_asset_job,
)
from dagster._core.definitions.utils import (
    config_from_files as config_from_files,
    config_from_pkg_resources as config_from_pkg_resources,
    config_from_yaml_strings as config_from_yaml_strings,
)
from dagster._core.errors import (
    DagsterConfigMappingFunctionError as DagsterConfigMappingFunctionError,
    DagsterError as DagsterError,
    DagsterEventLogInvalidForRun as DagsterEventLogInvalidForRun,
    DagsterExecutionInterruptedError as DagsterExecutionInterruptedError,
    DagsterExecutionStepExecutionError as DagsterExecutionStepExecutionError,
    DagsterExecutionStepNotFoundError as DagsterExecutionStepNotFoundError,
    DagsterInvalidConfigDefinitionError as DagsterInvalidConfigDefinitionError,
    DagsterInvalidConfigError as DagsterInvalidConfigError,
    DagsterInvalidDefinitionError as DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError as DagsterInvalidInvocationError,
    DagsterInvalidSubsetError as DagsterInvalidSubsetError,
    DagsterInvariantViolationError as DagsterInvariantViolationError,
    DagsterResourceFunctionError as DagsterResourceFunctionError,
    DagsterRunNotFoundError as DagsterRunNotFoundError,
    DagsterStepOutputNotFoundError as DagsterStepOutputNotFoundError,
    DagsterSubprocessError as DagsterSubprocessError,
    DagsterTypeCheckDidNotPass as DagsterTypeCheckDidNotPass,
    DagsterTypeCheckError as DagsterTypeCheckError,
    DagsterUnknownPartitionError as DagsterUnknownPartitionError,
    DagsterUnknownResourceError as DagsterUnknownResourceError,
    DagsterUnmetExecutorRequirementsError as DagsterUnmetExecutorRequirementsError,
    DagsterUserCodeExecutionError as DagsterUserCodeExecutionError,
    raise_execution_interrupts as raise_execution_interrupts,
)
from dagster._core.event_api import (
    AssetRecordsFilter as AssetRecordsFilter,
    EventLogRecord as EventLogRecord,
    EventRecordsFilter as EventRecordsFilter,
    EventRecordsResult as EventRecordsResult,
    RunShardedEventsCursor as RunShardedEventsCursor,
    RunStatusChangeRecordsFilter as RunStatusChangeRecordsFilter,
)
from dagster._core.events import (
    DagsterEvent as DagsterEvent,
    DagsterEventType as DagsterEventType,
)
from dagster._core.events.log import EventLogEntry as EventLogEntry
from dagster._core.execution.api import (
    ReexecutionOptions as ReexecutionOptions,
    execute_job as execute_job,
)
from dagster._core.execution.build_resources import build_resources as build_resources
from dagster._core.execution.context.compute import (
    AssetCheckExecutionContext as AssetCheckExecutionContext,
    AssetExecutionContext as AssetExecutionContext,
    OpExecutionContext as OpExecutionContext,
)
from dagster._core.execution.context.hook import (
    HookContext as HookContext,
    build_hook_context as build_hook_context,
)
from dagster._core.execution.context.init import (
    InitResourceContext as InitResourceContext,
    build_init_resource_context as build_init_resource_context,
)
from dagster._core.execution.context.input import (
    InputContext as InputContext,
    build_input_context as build_input_context,
)
from dagster._core.execution.context.invocation import (
    build_asset_context as build_asset_context,
    build_op_context as build_op_context,
)
from dagster._core.execution.context.logger import InitLoggerContext as InitLoggerContext
from dagster._core.execution.context.output import (
    OutputContext as OutputContext,
    build_output_context as build_output_context,
)
from dagster._core.execution.context.system import (
    DagsterTypeLoaderContext as DagsterTypeLoaderContext,
    StepExecutionContext as StepExecutionContext,
    TypeCheckContext as TypeCheckContext,
)
from dagster._core.execution.execute_in_process_result import (
    ExecuteInProcessResult as ExecuteInProcessResult,
)
from dagster._core.execution.job_execution_result import JobExecutionResult as JobExecutionResult
from dagster._core.execution.plan.external_step import (
    external_instance_from_step_run_ref as external_instance_from_step_run_ref,
    run_step_from_ref as run_step_from_ref,
    step_context_to_step_run_ref as step_context_to_step_run_ref,
    step_run_ref_to_step_context as step_run_ref_to_step_context,
)
from dagster._core.execution.validate_run_config import validate_run_config as validate_run_config
from dagster._core.execution.with_resources import with_resources as with_resources
from dagster._core.executor.base import Executor as Executor
from dagster._core.executor.init import InitExecutorContext as InitExecutorContext
from dagster._core.instance import DagsterInstance as DagsterInstance
from dagster._core.instance_for_test import instance_for_test as instance_for_test
from dagster._core.launcher.default_run_launcher import DefaultRunLauncher as DefaultRunLauncher
from dagster._core.log_manager import DagsterLogManager as DagsterLogManager
from dagster._core.pipes.client import (
    PipesClient as PipesClient,
    PipesContextInjector as PipesContextInjector,
    PipesExecutionResult as PipesExecutionResult,
    PipesMessageReader as PipesMessageReader,
)
from dagster._core.pipes.context import (
    PipesMessageHandler as PipesMessageHandler,
    PipesSession as PipesSession,
)
from dagster._core.pipes.subprocess import PipesSubprocessClient as PipesSubprocessClient
from dagster._core.pipes.utils import (
    PipesBlobStoreMessageReader as PipesBlobStoreMessageReader,
    PipesEnvContextInjector as PipesEnvContextInjector,
    PipesFileContextInjector as PipesFileContextInjector,
    PipesFileMessageReader as PipesFileMessageReader,
    PipesLogReader as PipesLogReader,
    PipesTempFileContextInjector as PipesTempFileContextInjector,
    PipesTempFileMessageReader as PipesTempFileMessageReader,
    open_pipes_session as open_pipes_session,
)
from dagster._core.run_coordinator.queued_run_coordinator import (
    QueuedRunCoordinator as QueuedRunCoordinator,
    SubmitRunContext as SubmitRunContext,
)
from dagster._core.storage.asset_value_loader import AssetValueLoader as AssetValueLoader
from dagster._core.storage.dagster_run import (
    DagsterRun as DagsterRun,
    DagsterRunStatus as DagsterRunStatus,
    RunRecord as RunRecord,
    RunsFilter as RunsFilter,
)
from dagster._core.storage.file_manager import (
    FileHandle as FileHandle,
    LocalFileHandle as LocalFileHandle,
    local_file_manager as local_file_manager,
)
from dagster._core.storage.fs_io_manager import (
    FilesystemIOManager as FilesystemIOManager,
    custom_path_fs_io_manager as custom_path_fs_io_manager,
    fs_io_manager as fs_io_manager,
)
from dagster._core.storage.input_manager import (
    InputManager as InputManager,
    InputManagerDefinition as InputManagerDefinition,
    input_manager as input_manager,
)
from dagster._core.storage.io_manager import (
    IOManager as IOManager,
    IOManagerDefinition as IOManagerDefinition,
    io_manager as io_manager,
)
from dagster._core.storage.mem_io_manager import (
    InMemoryIOManager as InMemoryIOManager,
    mem_io_manager as mem_io_manager,
)
from dagster._core.storage.partition_status_cache import (
    AssetPartitionStatus as AssetPartitionStatus,
)
from dagster._core.storage.tags import MAX_RUNTIME_SECONDS_TAG as MAX_RUNTIME_SECONDS_TAG
from dagster._core.storage.upath_io_manager import UPathIOManager as UPathIOManager
from dagster._core.types.config_schema import (
    DagsterTypeLoader as DagsterTypeLoader,
    dagster_type_loader as dagster_type_loader,
)
from dagster._core.types.dagster_type import (
    DagsterType as DagsterType,
    List as List,
    Optional as Optional,
    PythonObjectDagsterType as PythonObjectDagsterType,
    make_python_type_usable_as_dagster_type as make_python_type_usable_as_dagster_type,
)
from dagster._core.types.decorator import usable_as_dagster_type as usable_as_dagster_type
from dagster._core.types.python_dict import Dict as Dict
from dagster._core.types.python_set import Set as Set
from dagster._core.types.python_tuple import Tuple as Tuple
from dagster._loggers import (
    JsonLogFormatter as JsonLogFormatter,
    colored_console_logger as colored_console_logger,
    default_loggers as default_loggers,
    default_system_loggers as default_system_loggers,
    json_console_logger as json_console_logger,
)
from dagster._serdes.serdes import (
    deserialize_value as deserialize_value,
    serialize_value as serialize_value,
)
from dagster._utils import file_relative_path as file_relative_path
from dagster._utils.alert import (
    make_email_on_run_failure_sensor as make_email_on_run_failure_sensor,
)
from dagster._utils.dagster_type import check_dagster_type as check_dagster_type
from dagster._utils.log import get_dagster_logger as get_dagster_logger
from dagster._utils.warnings import (
    ConfigArgumentWarning as ConfigArgumentWarning,
)
from dagster.version import __version__ as __version__

# ruff: isort: split

# ########################
# ##### DYNAMIC IMPORTS
# ########################

import importlib
from collections.abc import Mapping, Sequence
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    Any as TypingAny,
    Callable,
    Final,
    Tuple as TypingTuple,  # noqa: F401
)

from dagster._utils.warnings import deprecation_warning

# NOTE: Unfortunately we have to declare deprecated aliases twice-- the
# TYPE_CHECKING declaration satisfies linters and type checkers, but the entry
# in `_DEPRECATED` is required  for us to generate the deprecation warning.

if TYPE_CHECKING:
    ##### EXAMPLE
    # from dagster.some.module import (
    #     Foo as Foo,
    # )
    pass  # noqa: TC005


_DEPRECATED: Final[Mapping[str, tuple[str, str, str]]] = {
    ##### EXAMPLE
    # "Foo": (
    #     "dagster.some.module",
    #     "1.1.0",  # breaking version
    #     "Use Bar instead.",
    # ),
}

_DEPRECATED_RENAMED: Final[Mapping[str, tuple[Callable, str]]] = {
    ##### EXAMPLE
    # "Foo": (Bar, "1.1.0"),
}


def __getattr__(name: str) -> TypingAny:
    if name in _DEPRECATED:
        module, breaking_version, additional_warn_text = _DEPRECATED[name]
        value = getattr(importlib.import_module(module), name)
        stacklevel = 3 if sys.version_info >= (3, 7) else 4
        deprecation_warning(name, breaking_version, additional_warn_text, stacklevel=stacklevel)
        return value
    elif name in _DEPRECATED_RENAMED:
        value, breaking_version = _DEPRECATED_RENAMED[name]
        stacklevel = 3 if sys.version_info >= (3, 7) else 4
        deprecation_warning(
            value.__name__,
            breaking_version,
            additional_warn_text=f"Use `{name}` instead.",
            stacklevel=stacklevel,
        )
        return value
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> Sequence[str]:
    return [*globals(), *_DEPRECATED.keys(), *_DEPRECATED_RENAMED.keys()]
