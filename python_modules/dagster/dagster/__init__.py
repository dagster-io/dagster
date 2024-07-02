import sys

from . import _module_alias_map

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

from dagster._utils import file_relative_path as file_relative_path
from dagster.version import __version__ as __version__
from dagster._loggers import (
    default_loggers as default_loggers,
    json_console_logger as json_console_logger,
    colored_console_logger as colored_console_logger,
    default_system_loggers as default_system_loggers,
)
from dagster._builtins import (
    Any as Any,
    Int as Int,
    Bool as Bool,
    Float as Float,
    String as String,
    Nothing as Nothing,
)
from dagster._utils.log import get_dagster_logger as get_dagster_logger
from dagster._core.errors import (
    DagsterError as DagsterError,
    DagsterTypeCheckError as DagsterTypeCheckError,
    DagsterSubprocessError as DagsterSubprocessError,
    DagsterRunNotFoundError as DagsterRunNotFoundError,
    DagsterInvalidConfigError as DagsterInvalidConfigError,
    DagsterInvalidSubsetError as DagsterInvalidSubsetError,
    DagsterTypeCheckDidNotPass as DagsterTypeCheckDidNotPass,
    DagsterUnknownResourceError as DagsterUnknownResourceError,
    DagsterEventLogInvalidForRun as DagsterEventLogInvalidForRun,
    DagsterResourceFunctionError as DagsterResourceFunctionError,
    DagsterUnknownPartitionError as DagsterUnknownPartitionError,
    DagsterInvalidDefinitionError as DagsterInvalidDefinitionError,
    DagsterInvalidInvocationError as DagsterInvalidInvocationError,
    DagsterUserCodeExecutionError as DagsterUserCodeExecutionError,
    DagsterInvariantViolationError as DagsterInvariantViolationError,
    DagsterStepOutputNotFoundError as DagsterStepOutputNotFoundError,
    DagsterExecutionInterruptedError as DagsterExecutionInterruptedError,
    DagsterConfigMappingFunctionError as DagsterConfigMappingFunctionError,
    DagsterExecutionStepNotFoundError as DagsterExecutionStepNotFoundError,
    DagsterExecutionStepExecutionError as DagsterExecutionStepExecutionError,
    DagsterInvalidConfigDefinitionError as DagsterInvalidConfigDefinitionError,
    DagsterUnmetExecutorRequirementsError as DagsterUnmetExecutorRequirementsError,
    raise_execution_interrupts as raise_execution_interrupts,
)
from dagster._core.events import (
    DagsterEvent as DagsterEvent,
    DagsterEventType as DagsterEventType,
)
from dagster._utils.alert import (
    make_email_on_run_failure_sensor as make_email_on_run_failure_sensor,
)
from dagster._config.field import Field as Field
from dagster._config.source import (
    IntSource as IntSource,
    BoolSource as BoolSource,
    StringSource as StringSource,
)
from dagster._core.instance import DagsterInstance as DagsterInstance
from dagster._serdes.serdes import (
    serialize_value as serialize_value,
    deserialize_value as deserialize_value,
)
from dagster._core.event_api import (
    EventLogRecord as EventLogRecord,
    AssetRecordsFilter as AssetRecordsFilter,
    EventRecordsFilter as EventRecordsFilter,
    EventRecordsResult as EventRecordsResult,
    RunShardedEventsCursor as RunShardedEventsCursor,
    RunStatusChangeRecordsFilter as RunStatusChangeRecordsFilter,
)
from dagster._utils.warnings import (
    ExperimentalWarning as ExperimentalWarning,
    ConfigArgumentWarning as ConfigArgumentWarning,
)
from dagster._core.events.log import EventLogEntry as EventLogEntry
from dagster._core.definitions import AssetCheckResult as AssetCheckResult
from dagster._core.log_manager import DagsterLogManager as DagsterLogManager
from dagster._core.pipes.utils import (
    PipesLogReader as PipesLogReader,
    PipesFileMessageReader as PipesFileMessageReader,
    PipesEnvContextInjector as PipesEnvContextInjector,
    PipesFileContextInjector as PipesFileContextInjector,
    PipesTempFileMessageReader as PipesTempFileMessageReader,
    PipesBlobStoreMessageReader as PipesBlobStoreMessageReader,
    PipesTempFileContextInjector as PipesTempFileContextInjector,
    open_pipes_session as open_pipes_session,
)
from dagster._core.pipes.client import (
    PipesClient as PipesClient,
    PipesMessageReader as PipesMessageReader,
    PipesContextInjector as PipesContextInjector,
)
from dagster._core.storage.tags import (
    MEMOIZED_RUN_TAG as MEMOIZED_RUN_TAG,
    MAX_RUNTIME_SECONDS_TAG as MAX_RUNTIME_SECONDS_TAG,
)
from dagster._config.config_type import (
    Enum as Enum,
    Array as Array,
    Noneable as Noneable,
    EnumValue as EnumValue,
    ScalarUnion as ScalarUnion,
)
from dagster._config.field_utils import (
    Map as Map,
    Shape as Shape,
    EnvVar as EnvVar,
    Selector as Selector,
    Permissive as Permissive,
)
from dagster._core.execution.api import (
    ReexecutionOptions as ReexecutionOptions,
    execute_job as execute_job,
)
from dagster._core.executor.base import Executor as Executor
from dagster._core.executor.init import InitExecutorContext as InitExecutorContext
from dagster._core.pipes.context import (
    PipesSession as PipesSession,
    PipesMessageHandler as PipesMessageHandler,
)
from dagster._utils.dagster_type import check_dagster_type as check_dagster_type
from dagster._config.config_schema import ConfigSchema as ConfigSchema
from dagster._core.types.decorator import usable_as_dagster_type as usable_as_dagster_type
from dagster._core.pipes.subprocess import PipesSubprocessClient as PipesSubprocessClient
from dagster._core.types.python_set import Set as Set
from dagster._config.pythonic_config import (
    Config as Config,
    PermissiveConfig as PermissiveConfig,
    ResourceDependency as ResourceDependency,
    ConfigurableResource as ConfigurableResource,
    ConfigurableIOManager as ConfigurableIOManager,
    ConfigurableIOManagerFactory as ConfigurableIOManagerFactory,
    IAttachDifferentObjectToOpContext as IAttachDifferentObjectToOpContext,
    ConfigurableLegacyIOManagerAdapter as ConfigurableLegacyIOManagerAdapter,
)
from dagster._core.definitions.input import (
    In as In,
    GraphIn as GraphIn,
    InputMapping as InputMapping,
)
from dagster._core.definitions.utils import (
    config_from_files as config_from_files,
    config_from_yaml_strings as config_from_yaml_strings,
    config_from_pkg_resources as config_from_pkg_resources,
)
from dagster._core.instance_for_test import instance_for_test as instance_for_test
from dagster._core.types.python_dict import Dict as Dict
from dagster._core.definitions.assets import AssetsDefinition as AssetsDefinition
from dagster._core.definitions.config import ConfigMapping as ConfigMapping
from dagster._core.definitions.events import (
    Output as Output,
    Failure as Failure,
    AssetKey as AssetKey,
    TypeCheck as TypeCheck,
    DynamicOutput as DynamicOutput,
    RetryRequested as RetryRequested,
    AssetObservation as AssetObservation,
    ExpectationResult as ExpectationResult,
    AssetMaterialization as AssetMaterialization,
)
from dagster._core.definitions.output import (
    Out as Out,
    GraphOut as GraphOut,
    DynamicOut as DynamicOut,
    OutputMapping as OutputMapping,
)
from dagster._core.definitions.policy import (
    Jitter as Jitter,
    Backoff as Backoff,
    RetryPolicy as RetryPolicy,
)
from dagster._core.definitions.result import (
    ObserveResult as ObserveResult,
    MaterializeResult as MaterializeResult,
)
from dagster._core.storage.io_manager import (
    IOManager as IOManager,
    IOManagerDefinition as IOManagerDefinition,
    io_manager as io_manager,
)
from dagster._core.types.dagster_type import (
    List as List,
    Optional as Optional,
    DagsterType as DagsterType,
    PythonObjectDagsterType as PythonObjectDagsterType,
    make_python_type_usable_as_dagster_type as make_python_type_usable_as_dagster_type,
)
from dagster._core.types.python_tuple import Tuple as Tuple
from dagster._core.storage.dagster_run import (
    RunRecord as RunRecord,
    DagsterRun as DagsterRun,
    RunsFilter as RunsFilter,
    DagsterRunStatus as DagsterRunStatus,
)
from dagster._core.types.config_schema import (
    DagsterTypeLoader as DagsterTypeLoader,
    dagster_type_loader as dagster_type_loader,
)
from dagster._core.definitions.asset_in import AssetIn as AssetIn
from dagster._core.definitions.metadata import (
    MetadataEntry as MetadataEntry,
    MetadataValue as MetadataValue,
    IntMetadataValue as IntMetadataValue,
    UrlMetadataValue as UrlMetadataValue,
    BoolMetadataValue as BoolMetadataValue,
    JsonMetadataValue as JsonMetadataValue,
    NullMetadataValue as NullMetadataValue,
    PathMetadataValue as PathMetadataValue,
    TextMetadataValue as TextMetadataValue,
    FloatMetadataValue as FloatMetadataValue,
    TableMetadataValue as TableMetadataValue,
    MarkdownMetadataValue as MarkdownMetadataValue,
    NotebookMetadataValue as NotebookMetadataValue,
    TimestampMetadataValue as TimestampMetadataValue,
    DagsterJobMetadataValue as DagsterJobMetadataValue,
    DagsterRunMetadataValue as DagsterRunMetadataValue,
    TableSchemaMetadataValue as TableSchemaMetadataValue,
    DagsterAssetMetadataValue as DagsterAssetMetadataValue,
    PythonArtifactMetadataValue as PythonArtifactMetadataValue,
    TableColumnLineageMetadataValue as TableColumnLineageMetadataValue,
)
from dagster._core.definitions.selector import (
    JobSelector as JobSelector,
    RepositorySelector as RepositorySelector,
    CodeLocationSelector as CodeLocationSelector,
)
from dagster._core.storage.file_manager import (
    FileHandle as FileHandle,
    LocalFileHandle as LocalFileHandle,
    local_file_manager as local_file_manager,
)
from dagster._core.definitions.asset_dep import AssetDep as AssetDep
from dagster._core.definitions.asset_out import AssetOut as AssetOut
from dagster._core.definitions.partition import (
    Partition as Partition,
    PartitionedConfig as PartitionedConfig,
    PartitionsDefinition as PartitionsDefinition,
    StaticPartitionsDefinition as StaticPartitionsDefinition,
    DynamicPartitionsDefinition as DynamicPartitionsDefinition,
    partitioned_config as partitioned_config,
    static_partitioned_config as static_partitioned_config,
    dynamic_partitioned_config as dynamic_partitioned_config,
)
from dagster._core.storage.fs_io_manager import (
    FilesystemIOManager as FilesystemIOManager,
    fs_io_manager as fs_io_manager,
    custom_path_fs_io_manager as custom_path_fs_io_manager,
)
from dagster._core.storage.input_manager import (
    InputManager as InputManager,
    InputManagerDefinition as InputManagerDefinition,
    input_manager as input_manager,
)
from dagster._core.definitions.asset_spec import AssetSpec as AssetSpec
from dagster._core.definitions.dependency import (
    NodeInvocation as NodeInvocation,
    DependencyDefinition as DependencyDefinition,
    MultiDependencyDefinition as MultiDependencyDefinition,
)
from dagster._core.definitions.run_config import RunConfig as RunConfig
from dagster._core.execution.context.hook import (
    HookContext as HookContext,
    build_hook_context as build_hook_context,
)
from dagster._core.execution.context.init import (
    InitResourceContext as InitResourceContext,
    build_init_resource_context as build_init_resource_context,
)
from dagster._core.storage.mem_io_manager import (
    InMemoryIOManager as InMemoryIOManager,
    mem_io_manager as mem_io_manager,
)
from dagster._core.definitions.composition import PendingNodeInvocation as PendingNodeInvocation
from dagster._core.definitions.materialize import (
    materialize as materialize,
    materialize_to_memory as materialize_to_memory,
)
from dagster._core.definitions.reconstruct import (
    reconstructable as reconstructable,
    build_reconstructable_job as build_reconstructable_job,
)
from dagster._core.definitions.run_request import (
    RunRequest as RunRequest,
    SkipReason as SkipReason,
    SensorResult as SensorResult,
    AddDynamicPartitionsRequest as AddDynamicPartitionsRequest,
    DeleteDynamicPartitionsRequest as DeleteDynamicPartitionsRequest,
)
from dagster._core.execution.context.input import (
    InputContext as InputContext,
    build_input_context as build_input_context,
)
from dagster._core.definitions.asset_checks import AssetChecksDefinition as AssetChecksDefinition
from dagster._core.definitions.configurable import configured as configured
from dagster._core.definitions.data_version import (
    DataVersion as DataVersion,
    DataProvenance as DataProvenance,
    DataVersionsByPartition as DataVersionsByPartition,
)
from dagster._core.definitions.source_asset import SourceAsset as SourceAsset
from dagster._core.execution.context.logger import InitLoggerContext as InitLoggerContext
from dagster._core.execution.context.output import (
    OutputContext as OutputContext,
    build_output_context as build_output_context,
)
from dagster._core.execution.context.system import (
    TypeCheckContext as TypeCheckContext,
    StepExecutionContext as StepExecutionContext,
    DagsterTypeLoaderContext as DagsterTypeLoaderContext,
)
from dagster._core.execution.with_resources import with_resources as with_resources
from dagster._core.storage.upath_io_manager import UPathIOManager as UPathIOManager
from dagster._core.definitions.op_definition import OpDefinition as OpDefinition
from dagster._core.definitions.step_launcher import (
    StepRunRef as StepRunRef,
    StepLauncher as StepLauncher,
)
from dagster._core.execution.build_resources import build_resources as build_resources
from dagster._core.execution.context.compute import (
    OpExecutionContext as OpExecutionContext,
    AssetExecutionContext as AssetExecutionContext,
    AssetCheckExecutionContext as AssetCheckExecutionContext,
)
from dagster._core.definitions.external_asset import (
    external_asset_from_spec as external_asset_from_spec,
    external_assets_from_specs as external_assets_from_specs,
)
from dagster._core.definitions.job_definition import JobDefinition as JobDefinition
from dagster._core.definitions.metadata.table import (
    TableColumn as TableColumn,
    TableRecord as TableRecord,
    TableSchema as TableSchema,
    TableColumnDep as TableColumnDep,
    TableConstraints as TableConstraints,
    TableColumnLineage as TableColumnLineage,
    TableColumnConstraints as TableColumnConstraints,
)
from dagster._core.storage.asset_value_loader import AssetValueLoader as AssetValueLoader
from dagster._core.definitions.asset_selection import AssetSelection as AssetSelection
from dagster._core.definitions.backfill_policy import BackfillPolicy as BackfillPolicy
from dagster._core.definitions.hook_definition import HookDefinition as HookDefinition
from dagster._core.definitions.asset_check_spec import (
    AssetCheckKey as AssetCheckKey,
    AssetCheckSpec as AssetCheckSpec,
    AssetCheckSeverity as AssetCheckSeverity,
)
from dagster._core.definitions.freshness_policy import FreshnessPolicy as FreshnessPolicy
from dagster._core.definitions.graph_definition import GraphDefinition as GraphDefinition
from dagster._core.definitions.version_strategy import (
    VersionStrategy as VersionStrategy,
    OpVersionContext as OpVersionContext,
    ResourceVersionContext as ResourceVersionContext,
    SourceHashVersionStrategy as SourceHashVersionStrategy,
)
from dagster._core.execution.context.invocation import (
    build_op_context as build_op_context,
    build_asset_context as build_asset_context,
)
from dagster._core.execution.plan.external_step import (
    run_step_from_ref as run_step_from_ref,
    step_context_to_step_run_ref as step_context_to_step_run_ref,
    step_run_ref_to_step_context as step_run_ref_to_step_context,
    external_instance_from_step_run_ref as external_instance_from_step_run_ref,
)
from dagster._core.definitions.definitions_class import (
    Definitions as Definitions,
    BindResourcesToJobs as BindResourcesToJobs,
    create_repository_using_definitions_args as create_repository_using_definitions_args,
)
from dagster._core.definitions.logger_definition import (
    LoggerDefinition as LoggerDefinition,
    logger as logger,
    build_init_logger_context as build_init_logger_context,
)
from dagster._core.definitions.partition_mapping import (
    PartitionMapping as PartitionMapping,
    AllPartitionMapping as AllPartitionMapping,
    LastPartitionMapping as LastPartitionMapping,
    MultiPartitionMapping as MultiPartitionMapping,
    StaticPartitionMapping as StaticPartitionMapping,
    IdentityPartitionMapping as IdentityPartitionMapping,
    DimensionPartitionMapping as DimensionPartitionMapping,
    SpecificPartitionsPartitionMapping as SpecificPartitionsPartitionMapping,
    MultiToSingleDimensionPartitionMapping as MultiToSingleDimensionPartitionMapping,
)
from dagster._core.definitions.sensor_definition import (
    SensorDefinition as SensorDefinition,
    DefaultSensorStatus as DefaultSensorStatus,
    SensorEvaluationContext as SensorEvaluationContext,
    build_sensor_context as build_sensor_context,
)
from dagster._core.execution.validate_run_config import validate_run_config as validate_run_config
from dagster._core.launcher.default_run_launcher import DefaultRunLauncher as DefaultRunLauncher
from dagster._core.storage.memoizable_io_manager import MemoizableIOManager as MemoizableIOManager
from dagster._core.execution.job_execution_result import JobExecutionResult as JobExecutionResult
from dagster._core.storage.partition_status_cache import (
    AssetPartitionStatus as AssetPartitionStatus,
)
from dagster._core.definitions.executor_definition import (
    ExecutorDefinition as ExecutorDefinition,
    ExecutorRequirement as ExecutorRequirement,
    executor as executor,
    in_process_executor as in_process_executor,
    multiprocess_executor as multiprocess_executor,
    multi_or_in_process_executor as multi_or_in_process_executor,
    multiple_process_executor_requirements as multiple_process_executor_requirements,
)
from dagster._core.definitions.partition_key_range import PartitionKeyRange as PartitionKeyRange
from dagster._core.definitions.resource_annotation import ResourceParam as ResourceParam
from dagster._core.definitions.resource_definition import (
    ResourceDefinition as ResourceDefinition,
    resource as resource,
    make_values_resource as make_values_resource,
)
from dagster._core.definitions.schedule_definition import (
    ScheduleDefinition as ScheduleDefinition,
    DefaultScheduleStatus as DefaultScheduleStatus,
    ScheduleEvaluationContext as ScheduleEvaluationContext,
    build_schedule_context as build_schedule_context,
)
from dagster._core.definitions.partitioned_schedule import (
    build_schedule_from_partitioned_job as build_schedule_from_partitioned_job,
)
from dagster._core.definitions.auto_materialize_rule import (
    AutoMaterializeRule as AutoMaterializeRule,
)
from dagster._core.definitions.repository_definition import (
    RepositoryData as RepositoryData,
    RepositoryDefinition as RepositoryDefinition,
)
from dagster._core.definitions.declarative_automation import (
    AssetCondition as AssetCondition,
    AutomationCondition as AutomationCondition,
    evaluate_automation_conditions as evaluate_automation_conditions,
)
from dagster._core.definitions.time_window_partitions import (
    TimeWindow as TimeWindow,
    DailyPartitionsDefinition as DailyPartitionsDefinition,
    HourlyPartitionsDefinition as HourlyPartitionsDefinition,
    WeeklyPartitionsDefinition as WeeklyPartitionsDefinition,
    MonthlyPartitionsDefinition as MonthlyPartitionsDefinition,
    TimeWindowPartitionsDefinition as TimeWindowPartitionsDefinition,
    daily_partitioned_config as daily_partitioned_config,
    hourly_partitioned_config as hourly_partitioned_config,
    weekly_partitioned_config as weekly_partitioned_config,
    monthly_partitioned_config as monthly_partitioned_config,
)
from dagster._core.definitions.asset_sensor_definition import (
    AssetSensorDefinition as AssetSensorDefinition,
)
from dagster._core.definitions.auto_materialize_policy import (
    AutoMaterializePolicy as AutoMaterializePolicy,
)
from dagster._core.definitions.decorators.op_decorator import op as op
from dagster._core.execution.execute_in_process_result import (
    ExecuteInProcessResult as ExecuteInProcessResult,
)
from dagster._core.definitions.decorators.job_decorator import job as job
from dagster._core.definitions.load_assets_from_modules import (
    load_assets_from_modules as load_assets_from_modules,
    load_assets_from_package_name as load_assets_from_package_name,
    load_assets_from_current_module as load_assets_from_current_module,
    load_assets_from_package_module as load_assets_from_package_module,
)
from dagster._core.definitions.decorators.hook_decorator import (
    failure_hook as failure_hook,
    success_hook as success_hook,
)
from dagster._core.definitions.decorators.asset_decorator import (
    asset as asset,
    graph_asset as graph_asset,
    multi_asset as multi_asset,
    graph_multi_asset as graph_multi_asset,
)
from dagster._core.definitions.decorators.graph_decorator import graph as graph
from dagster._core.run_coordinator.queued_run_coordinator import (
    SubmitRunContext as SubmitRunContext,
    QueuedRunCoordinator as QueuedRunCoordinator,
)
from dagster._core.definitions.auto_materialize_rule_impls import (
    AutoMaterializeAssetPartitionsFilter as AutoMaterializeAssetPartitionsFilter,
)
from dagster._core.definitions.decorators.sensor_decorator import (
    sensor as sensor,
    asset_sensor as asset_sensor,
    multi_asset_sensor as multi_asset_sensor,
)
from dagster._core.definitions.multi_dimensional_partitions import (
    MultiPartitionKey as MultiPartitionKey,
    MultiPartitionsDefinition as MultiPartitionsDefinition,
)
from dagster._core.definitions.run_status_sensor_definition import (
    RunStatusSensorContext as RunStatusSensorContext,
    RunFailureSensorContext as RunFailureSensorContext,
    RunStatusSensorDefinition as RunStatusSensorDefinition,
    run_status_sensor as run_status_sensor,
    run_failure_sensor as run_failure_sensor,
    build_run_status_sensor_context as build_run_status_sensor_context,
)
from dagster._core.definitions.decorators.schedule_decorator import schedule as schedule
from dagster._core.definitions.multi_asset_sensor_definition import (
    MultiAssetSensorDefinition as MultiAssetSensorDefinition,
    MultiAssetSensorEvaluationContext as MultiAssetSensorEvaluationContext,
    build_multi_asset_sensor_context as build_multi_asset_sensor_context,
)
from dagster._core.definitions.time_window_partition_mapping import (
    TimeWindowPartitionMapping as TimeWindowPartitionMapping,
)
from dagster._core.definitions.load_asset_checks_from_modules import (
    load_asset_checks_from_modules as load_asset_checks_from_modules,
    load_asset_checks_from_package_name as load_asset_checks_from_package_name,
    load_asset_checks_from_current_module as load_asset_checks_from_current_module,
    load_asset_checks_from_package_module as load_asset_checks_from_package_module,
)
from dagster._core.definitions.decorators.repository_decorator import repository as repository
from dagster._core.definitions.unresolved_asset_job_definition import (
    define_asset_job as define_asset_job,
)
from dagster._core.definitions.decorators.asset_check_decorator import (
    asset_check as asset_check,
    multi_asset_check as multi_asset_check,
)
from dagster._core.definitions.decorators.source_asset_decorator import (
    observable_source_asset as observable_source_asset,
    multi_observable_source_asset as multi_observable_source_asset,
)
from dagster._core.definitions.auto_materialize_sensor_definition import (
    AutoMaterializeSensorDefinition as AutoMaterializeSensorDefinition,
)
from dagster._core.definitions.freshness_policy_sensor_definition import (
    FreshnessPolicySensorContext as FreshnessPolicySensorContext,
    FreshnessPolicySensorDefinition as FreshnessPolicySensorDefinition,
    freshness_policy_sensor as freshness_policy_sensor,
    build_freshness_policy_sensor_context as build_freshness_policy_sensor_context,
)
from dagster._core.definitions.decorators.config_mapping_decorator import (
    config_mapping as config_mapping,
)
from dagster._core.definitions.asset_check_factories.schema_change_checks import (
    build_column_schema_change_checks as build_column_schema_change_checks,
)
from dagster._core.definitions.asset_check_factories.metadata_bounds_checks import (
    build_metadata_bounds_checks as build_metadata_bounds_checks,
)
from dagster._core.definitions.asset_check_factories.freshness_checks.sensor import (
    build_sensor_for_freshness_checks as build_sensor_for_freshness_checks,
)
from dagster._core.definitions.asset_check_factories.freshness_checks.last_update import (
    build_last_update_freshness_checks as build_last_update_freshness_checks,
)
from dagster._core.definitions.asset_check_factories.freshness_checks.time_partition import (
    build_time_partition_freshness_checks as build_time_partition_freshness_checks,
)

# ruff: isort: split

# ########################
# ##### DYNAMIC IMPORTS
# ########################

import importlib
from typing import (
    TYPE_CHECKING,
    Any as TypingAny,
    Tuple as TypingTuple,
    Mapping,
    Callable,
    Sequence,
)

from typing_extensions import Final

from dagster._utils.warnings import deprecation_warning

# NOTE: Unfortunately we have to declare deprecated aliases twice-- the
# TYPE_CHECKING declaration satisfies linters and type checkers, but the entry
# in `_DEPRECATED` is required  for us to generate the deprecation warning.

if TYPE_CHECKING:
    ##### EXAMPLE
    # from dagster.some.module import (
    #     Foo as Foo,
    # )
    pass  # noqa: TCH005


_DEPRECATED: Final[Mapping[str, TypingTuple[str, str, str]]] = {
    ##### EXAMPLE
    # "Foo": (
    #     "dagster.some.module",
    #     "1.1.0",  # breaking version
    #     "Use Bar instead.",
    # ),
}

_DEPRECATED_RENAMED: Final[Mapping[str, TypingTuple[Callable, str]]] = {
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
