from __future__ import annotations

import logging
import logging.config
import os
import sys
import time
import warnings
import weakref
from collections import defaultdict
from contextlib import ExitStack
from enum import Enum
from tempfile import TemporaryDirectory
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Dict,
    FrozenSet,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
    Union,
    cast,
)

import yaml

import dagster._check as check
from dagster._annotations import public
from dagster._config.field import Field
from dagster._core.definitions.events import AssetKey
from dagster._core.definitions.pipeline_base import InMemoryPipeline
from dagster._core.definitions.pipeline_definition import (
    PipelineDefinition,
    PipelineSubsetDefinition,
)
from dagster._core.errors import (
    DagsterHomeNotSetError,
    DagsterInvariantViolationError,
    DagsterRunAlreadyExists,
    DagsterRunConflict,
    DagsterUndefinedLogicalVersionError,
)
from dagster._core.storage.pipeline_run import (
    IN_PROGRESS_RUN_STATUSES,
    DagsterRun,
    JobBucket,
    PipelineRun,
    PipelineRunStatsSnapshot,
    PipelineRunStatus,
    RunPartitionData,
    RunRecord,
    RunsFilter,
    TagBucket,
)
from dagster._core.storage.tags import PARENT_RUN_ID_TAG, RESUME_RETRY_TAG, ROOT_RUN_ID_TAG
from dagster._core.system_config.objects import ResolvedRunConfig
from dagster._core.utils import str_format_list
from dagster._serdes import ConfigurableClass
from dagster._seven import get_current_datetime_in_utc
from dagster._utils import merge_dicts, traced
from dagster._utils.backcompat import deprecation_warning, experimental_functionality_warning
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.log import get_dagster_logger

from .config import (
    DAGSTER_CONFIG_YAML_FILENAME,
    DEFAULT_LOCAL_CODE_SERVER_STARTUP_TIMEOUT,
    get_default_tick_retention_settings,
    get_tick_retention_settings,
    is_dagster_home_set,
)
from .ref import InstanceRef

# 'airflow_execution_date' and 'is_airflow_ingest_pipeline' are hardcoded tags used in the
# airflow ingestion logic (see: dagster_pipeline_factory.py). 'airflow_execution_date' stores the
# 'execution_date' used in Airflow operator execution and 'is_airflow_ingest_pipeline' determines
# whether 'airflow_execution_date' is needed.
# https://github.com/dagster-io/dagster/issues/2403
AIRFLOW_EXECUTION_DATE_STR = "airflow_execution_date"
IS_AIRFLOW_INGEST_PIPELINE_STR = "is_airflow_ingest_pipeline"

if TYPE_CHECKING:
    from dagster._core.debug import DebugRunPayload
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.events import DagsterEvent, DagsterEventType
    from dagster._core.events.log import EventLogEntry
    from dagster._core.execution.backfill import PartitionBackfill
    from dagster._core.execution.plan.plan import ExecutionPlan
    from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
    from dagster._core.execution.stats import RunStepKeyStatsSnapshot
    from dagster._core.host_representation import (
        ExternalPipeline,
        ExternalSensor,
        HistoricalPipeline,
        RepositoryLocation,
    )
    from dagster._core.host_representation.origin import ExternalPipelineOrigin
    from dagster._core.launcher import RunLauncher
    from dagster._core.run_coordinator import RunCoordinator
    from dagster._core.scheduler import Scheduler
    from dagster._core.scheduler.instigation import (
        InstigatorState,
        InstigatorTick,
        TickData,
        TickStatus,
    )
    from dagster._core.secrets import SecretsLoader
    from dagster._core.snap import ExecutionPlanSnapshot, PipelineSnapshot
    from dagster._core.storage.captured_log_manager import CapturedLogManager
    from dagster._core.storage.compute_log_manager import ComputeLogManager
    from dagster._core.storage.event_log import EventLogStorage
    from dagster._core.storage.event_log.base import AssetRecord, EventLogRecord, EventRecordsFilter
    from dagster._core.storage.root import LocalArtifactStorage
    from dagster._core.storage.runs import RunStorage
    from dagster._core.storage.schedules import ScheduleStorage
    from dagster._core.workspace.workspace import IWorkspace
    from dagster._daemon.types import DaemonHeartbeat, DaemonStatus


def _check_run_equality(
    pipeline_run: PipelineRun, candidate_run: PipelineRun
) -> Mapping[str, Tuple[Any, Any]]:
    field_diff = {}
    for field in pipeline_run._fields:
        expected_value = getattr(pipeline_run, field)
        candidate_value = getattr(candidate_run, field)
        if expected_value != candidate_value:
            field_diff[field] = (expected_value, candidate_value)

    return field_diff


def _format_field_diff(field_diff: Mapping[str, Tuple[Any, Any]]) -> str:
    return "\n".join(
        [
            (
                "    {field_name}:\n"
                + "        Expected: {expected_value}\n"
                + "        Received: {candidate_value}"
            ).format(
                field_name=field_name,
                expected_value=expected_value,
                candidate_value=candidate_value,
            )
            for field_name, (
                expected_value,
                candidate_value,
            ) in field_diff.items()
        ]
    )


class _EventListenerLogHandler(logging.Handler):
    def __init__(self, instance):
        self._instance = instance
        super(_EventListenerLogHandler, self).__init__()

    def emit(self, record):
        from dagster._core.events import EngineEventData
        from dagster._core.events.log import StructuredLoggerMessage, construct_event_record

        event = construct_event_record(
            StructuredLoggerMessage(
                name=record.name,
                message=record.msg,
                level=record.levelno,
                meta=record.dagster_meta,  # type: ignore
                record=record,
            )
        )

        try:
            self._instance.handle_new_event(event)
        except Exception as e:
            sys.stderr.write(f"Exception while writing logger call to event log: {str(e)}\n")
            if event.dagster_event:
                # Swallow user-generated log failures so that the entire step/run doesn't fail, but
                # raise failures writing system-generated log events since they are the source of
                # truth for the state of the run
                raise
            elif event.run_id:
                self._instance.report_engine_event(
                    "Exception while writing logger call to event log",
                    pipeline_name=event.pipeline_name,
                    run_id=event.run_id,
                    step_key=event.step_key,
                    engine_event_data=EngineEventData(
                        error=serializable_error_info_from_exc_info(sys.exc_info()),
                    ),
                )


class InstanceType(Enum):
    PERSISTENT = "PERSISTENT"
    EPHEMERAL = "EPHEMERAL"


T_DagsterInstance = TypeVar("T_DagsterInstance", bound="DagsterInstance")


class MayHaveInstanceWeakref(Generic[T_DagsterInstance]):
    """Mixin for classes that can have a weakref back to a Dagster instance."""

    _instance_weakref: Optional[weakref.ReferenceType[T_DagsterInstance]]

    def __init__(self):
        self._instance_weakref = None

    @property
    def _instance(self) -> T_DagsterInstance:
        instance = (
            self._instance_weakref()
            # Backcompat with custom subclasses that don't call super().__init__()
            # in their own __init__ implementations
            if (hasattr(self, "_instance_weakref") and self._instance_weakref is not None)
            else None
        )
        return cast(T_DagsterInstance, instance)

    def register_instance(self, instance: T_DagsterInstance):
        check.invariant(
            # Backcompat with custom subclasses that don't call super().__init__()
            # in their own __init__ implementations
            (not hasattr(self, "_instance_weakref") or self._instance_weakref is None),
            "Must only call initialize once",
        )

        # Store a weakref to avoid a circular reference / enable GC
        self._instance_weakref = weakref.ref(instance)


class DagsterInstance:
    """Core abstraction for managing Dagster's access to storage and other resources.

    Use DagsterInstance.get() to grab the current DagsterInstance which will load based on
    the values in the ``dagster.yaml`` file in ``$DAGSTER_HOME``.

    Alternatively, DagsterInstance.ephemeral() can use used which provides a set of
    transient in-memory components.

    Configuration of this class should be done by setting values in ``$DAGSTER_HOME/dagster.yaml``.
    For example, to use Postgres for dagster storage, you can write a ``dagster.yaml`` such as the
    following:

    .. literalinclude:: ../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-pg.yaml
       :caption: dagster.yaml
       :language: YAML

    Args:
        instance_type (InstanceType): Indicates whether the instance is ephemeral or persistent.
            Users should not attempt to set this value directly or in their ``dagster.yaml`` files.
        local_artifact_storage (LocalArtifactStorage): The local artifact storage is used to
            configure storage for any artifacts that require a local disk, such as schedules, or
            when using the filesystem system storage to manage files and intermediates. By default,
            this will be a :py:class:`dagster._core.storage.root.LocalArtifactStorage`. Configurable
            in ``dagster.yaml`` using the :py:class:`~dagster.serdes.ConfigurableClass`
            machinery.
        run_storage (RunStorage): The run storage is used to store metadata about ongoing and past
            pipeline runs. By default, this will be a
            :py:class:`dagster._core.storage.runs.SqliteRunStorage`. Configurable in ``dagster.yaml``
            using the :py:class:`~dagster.serdes.ConfigurableClass` machinery.
        event_storage (EventLogStorage): Used to store the structured event logs generated by
            pipeline runs. By default, this will be a
            :py:class:`dagster._core.storage.event_log.SqliteEventLogStorage`. Configurable in
            ``dagster.yaml`` using the :py:class:`~dagster.serdes.ConfigurableClass` machinery.
        compute_log_manager (ComputeLogManager): The compute log manager handles stdout and stderr
            logging for solid compute functions. By default, this will be a
            :py:class:`dagster._core.storage.local_compute_log_manager.LocalComputeLogManager`.
            Configurable in ``dagster.yaml`` using the
            :py:class:`~dagster.serdes.ConfigurableClass` machinery.
        run_coordinator (RunCoordinator): A runs coordinator may be used to manage the execution
            of pipeline runs.
        run_launcher (Optional[RunLauncher]): Optionally, a run launcher may be used to enable
            a Dagster instance to launch pipeline runs, e.g. on a remote Kubernetes cluster, in
            addition to running them locally.
        settings (Optional[Dict]): Specifies certain per-instance settings,
            such as feature flags. These are set in the ``dagster.yaml`` under a set of whitelisted
            keys.
        ref (Optional[InstanceRef]): Used by internal machinery to pass instances across process
            boundaries.
    """

    _PROCESS_TEMPDIR: Optional[TemporaryDirectory] = None
    _EXIT_STACK = None

    def __init__(
        self,
        instance_type: InstanceType,
        local_artifact_storage: "LocalArtifactStorage",
        run_storage: "RunStorage",
        event_storage: "EventLogStorage",
        compute_log_manager: "ComputeLogManager",
        run_coordinator: "RunCoordinator",
        run_launcher: Optional["RunLauncher"],
        scheduler: Optional["Scheduler"] = None,
        schedule_storage: Optional["ScheduleStorage"] = None,
        settings: Optional[Mapping[str, Any]] = None,
        secrets_loader: Optional["SecretsLoader"] = None,
        ref: Optional[InstanceRef] = None,
    ):
        from dagster._core.launcher import RunLauncher
        from dagster._core.run_coordinator import RunCoordinator
        from dagster._core.scheduler import Scheduler
        from dagster._core.secrets import SecretsLoader
        from dagster._core.storage.captured_log_manager import CapturedLogManager
        from dagster._core.storage.compute_log_manager import ComputeLogManager
        from dagster._core.storage.event_log import EventLogStorage
        from dagster._core.storage.root import LocalArtifactStorage
        from dagster._core.storage.runs import RunStorage
        from dagster._core.storage.schedules import ScheduleStorage

        self._instance_type = check.inst_param(instance_type, "instance_type", InstanceType)
        self._local_artifact_storage = check.inst_param(
            local_artifact_storage, "local_artifact_storage", LocalArtifactStorage
        )
        self._event_storage = check.inst_param(event_storage, "event_storage", EventLogStorage)
        self._event_storage.register_instance(self)

        self._run_storage = check.inst_param(run_storage, "run_storage", RunStorage)
        self._run_storage.register_instance(self)

        self._compute_log_manager = check.inst_param(
            compute_log_manager, "compute_log_manager", ComputeLogManager
        )
        if not isinstance(self._compute_log_manager, CapturedLogManager):
            deprecation_warning(
                "ComputeLogManager", "1.2.0", "Implement the CapturedLogManager interface instead."
            )
        self._compute_log_manager.register_instance(self)
        self._scheduler = check.opt_inst_param(scheduler, "scheduler", Scheduler)

        self._schedule_storage = check.opt_inst_param(
            schedule_storage, "schedule_storage", ScheduleStorage
        )
        if self._schedule_storage:
            self._schedule_storage.register_instance(self)

        self._run_coordinator = check.inst_param(run_coordinator, "run_coordinator", RunCoordinator)
        self._run_coordinator.register_instance(self)

        if run_launcher:
            self._run_launcher: Optional[RunLauncher] = check.inst_param(
                run_launcher, "run_launcher", RunLauncher
            )
            run_launcher.register_instance(self)
        else:
            check.invariant(ref, "Run launcher must be provided if instance is not from a ref")
            self._run_launcher = None

        self._settings = check.opt_mapping_param(settings, "settings")

        self._secrets_loader = check.opt_inst_param(secrets_loader, "secrets_loader", SecretsLoader)

        if self._secrets_loader:
            self._secrets_loader.register_instance(self)

        self._ref = check.opt_inst_param(ref, "ref", InstanceRef)

        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)

        run_monitoring_enabled = self.run_monitoring_settings.get("enabled", False)
        if run_monitoring_enabled and not self.run_launcher.supports_check_run_worker_health:
            run_monitoring_enabled = False
            warnings.warn(
                "The configured run launcher does not support run monitoring, disabling it.",
            )
        self._run_monitoring_enabled = run_monitoring_enabled
        if self.run_monitoring_enabled and self.run_monitoring_max_resume_run_attempts:
            check.invariant(
                self.run_launcher.supports_resume_run,
                "The configured run launcher does not support resuming runs. "
                "Set max_resume_run_attempts to 0 to use run monitoring. Any runs with a failed run "
                "worker will be marked as failed, but will not be resumed.",
            )

        if self.run_retries_enabled:
            check.invariant(
                self.run_storage.supports_kvs(),
                "Run retries are enabled, but the configured run storage does not support them. "
                "Consider switching to Postgres or Mysql.",
            )
            check.invariant(
                self.event_log_storage.supports_event_consumer_queries(),
                "Run retries are enabled, but the configured event log storage does not support them. "
                "Consider switching to Postgres or Mysql.",
            )

    # ctors

    @public
    @staticmethod
    def ephemeral(
        tempdir: Optional[str] = None, preload: Optional[Sequence["DebugRunPayload"]] = None
    ) -> "DagsterInstance":
        from dagster._core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
        from dagster._core.run_coordinator import DefaultRunCoordinator
        from dagster._core.storage.event_log import InMemoryEventLogStorage
        from dagster._core.storage.noop_compute_log_manager import NoOpComputeLogManager
        from dagster._core.storage.root import LocalArtifactStorage
        from dagster._core.storage.runs import InMemoryRunStorage

        if tempdir is None:
            tempdir = DagsterInstance.temp_storage()

        return DagsterInstance(
            instance_type=InstanceType.EPHEMERAL,
            local_artifact_storage=LocalArtifactStorage(tempdir),
            run_storage=InMemoryRunStorage(preload=preload),
            event_storage=InMemoryEventLogStorage(preload=preload),
            compute_log_manager=NoOpComputeLogManager(),
            run_coordinator=DefaultRunCoordinator(),
            run_launcher=SyncInMemoryRunLauncher(),
        )

    @public
    @staticmethod
    def get() -> "DagsterInstance":
        dagster_home_path = os.getenv("DAGSTER_HOME")

        if not dagster_home_path:
            raise DagsterHomeNotSetError(
                (
                    "The environment variable $DAGSTER_HOME is not set. \n"
                    "Dagster requires this environment variable to be set to an existing directory in your filesystem. "
                    "This directory is used to store metadata across sessions, or load the dagster.yaml "
                    "file which can configure storing metadata in an external database.\n"
                    "You can resolve this error by exporting the environment variable. For example, you can run the following command in your shell or include it in your shell configuration file:\n"
                    '\texport DAGSTER_HOME=~"/dagster_home"\n'
                    "or PowerShell\n"
                    "$env:DAGSTER_HOME = ($home + '\\dagster_home')"
                    "or batch"
                    "set DAGSTER_HOME=%UserProfile%/dagster_home"
                    "Alternatively, DagsterInstance.ephemeral() can be used for a transient instance.\n"
                )
            )

        dagster_home_path = os.path.expanduser(dagster_home_path)

        if not os.path.isabs(dagster_home_path):
            raise DagsterInvariantViolationError(
                (
                    '$DAGSTER_HOME "{}" must be an absolute path. Dagster requires this '
                    "environment variable to be set to an existing directory in your filesystem."
                ).format(dagster_home_path)
            )

        if not (os.path.exists(dagster_home_path) and os.path.isdir(dagster_home_path)):
            raise DagsterInvariantViolationError(
                (
                    '$DAGSTER_HOME "{}" is not a directory or does not exist. Dagster requires this '
                    "environment variable to be set to an existing directory in your filesystem"
                ).format(dagster_home_path)
            )

        return DagsterInstance.from_config(dagster_home_path)

    @public
    @staticmethod
    def local_temp(tempdir=None, overrides=None) -> "DagsterInstance":
        if tempdir is None:
            tempdir = DagsterInstance.temp_storage()

        return DagsterInstance.from_ref(InstanceRef.from_dir(tempdir, overrides=overrides))

    @staticmethod
    def from_config(
        config_dir: str,
        config_filename: str = DAGSTER_CONFIG_YAML_FILENAME,
    ) -> "DagsterInstance":
        instance_ref = InstanceRef.from_dir(config_dir, config_filename=config_filename)
        return DagsterInstance.from_ref(instance_ref)

    @staticmethod
    def from_ref(instance_ref: InstanceRef) -> "DagsterInstance":
        check.inst_param(instance_ref, "instance_ref", InstanceRef)

        # DagsterInstance doesn't implement ConfigurableClass, but we may still sometimes want to
        # have custom subclasses of DagsterInstance. This machinery allows for those custom
        # subclasses to receive additional keyword arguments passed through the config YAML.
        klass = instance_ref.custom_instance_class or DagsterInstance
        kwargs = instance_ref.custom_instance_class_config

        unified_storage = instance_ref.storage
        run_storage = unified_storage.run_storage if unified_storage else instance_ref.run_storage
        event_storage = (
            unified_storage.event_log_storage if unified_storage else instance_ref.event_storage
        )
        schedule_storage = (
            unified_storage.schedule_storage if unified_storage else instance_ref.schedule_storage
        )

        return klass(  # type: ignore
            instance_type=InstanceType.PERSISTENT,
            local_artifact_storage=instance_ref.local_artifact_storage,
            run_storage=run_storage,
            event_storage=event_storage,
            schedule_storage=schedule_storage,
            compute_log_manager=instance_ref.compute_log_manager,
            scheduler=instance_ref.scheduler,
            run_coordinator=instance_ref.run_coordinator,
            run_launcher=None,  # lazy load
            settings=instance_ref.settings,
            secrets_loader=instance_ref.secrets_loader,
            ref=instance_ref,
            **kwargs,
        )

    # flags

    @property
    def is_persistent(self) -> bool:
        return self._instance_type == InstanceType.PERSISTENT

    @property
    def is_ephemeral(self) -> bool:
        return self._instance_type == InstanceType.EPHEMERAL

    def get_ref(self) -> InstanceRef:
        if self._ref:
            return self._ref

        check.failed(
            "Attempted to prepare an ineligible DagsterInstance ({inst_type}) for cross "
            "process communication.{dagster_home_msg}".format(
                inst_type=self._instance_type,
                dagster_home_msg="\nDAGSTER_HOME environment variable is not set, set it to "
                "a directory on the filesystem for dagster to use for storage and cross "
                "process coordination."
                if os.getenv("DAGSTER_HOME") is None
                else "",
            )
        )

    @property
    def root_directory(self) -> str:
        return self._local_artifact_storage.base_dir

    @staticmethod
    def temp_storage() -> str:
        from dagster._core.test_utils import environ

        if DagsterInstance._PROCESS_TEMPDIR is None:
            DagsterInstance._EXIT_STACK = ExitStack()
            DagsterInstance._EXIT_STACK.enter_context(
                environ({"DAGSTER_TELEMETRY_DISABLED": "yes"})
            )
            DagsterInstance._PROCESS_TEMPDIR = TemporaryDirectory()
        return cast(TemporaryDirectory, DagsterInstance._PROCESS_TEMPDIR).name

    def _info(self, component):
        # ConfigurableClass may not have inst_data if it's a direct instantiation
        # which happens for ephemeral instances
        if isinstance(component, ConfigurableClass) and component.inst_data:
            return component.inst_data.info_dict()
        if type(component) is dict:
            return component
        return component.__class__.__name__

    def _info_str_for_component(self, component_name, component):
        return yaml.dump(
            {component_name: self._info(component)}, default_flow_style=False, sort_keys=False
        )

    def info_dict(self):

        settings = self._settings if self._settings else {}

        ret = {
            "local_artifact_storage": self._info(self._local_artifact_storage),
            "run_storage": self._info(self._run_storage),
            "event_log_storage": self._info(self._event_storage),
            "compute_logs": self._info(self._compute_log_manager),
            "schedule_storage": self._info(self._schedule_storage),
            "scheduler": self._info(self._scheduler),
            "run_coordinator": self._info(self._run_coordinator),
            "run_launcher": self._info(self.run_launcher),
        }
        ret.update(
            {
                settings_key: self._info(settings_value)
                for settings_key, settings_value in settings.items()
            }
        )

        return ret

    def info_str(self) -> str:
        return yaml.dump(self.info_dict(), default_flow_style=False, sort_keys=False)

    def schema_str(self) -> str:
        def _schema_dict(alembic_version):
            if not alembic_version:
                return None
            db_revision, head_revision = alembic_version
            return {
                "current": db_revision,
                "latest": head_revision,
            }

        return yaml.dump(
            {
                "schema": {
                    "event_log_storage": _schema_dict(self._event_storage.alembic_version()),
                    "run_storage": _schema_dict(self._event_storage.alembic_version()),
                    "schedule_storage": _schema_dict(self._event_storage.alembic_version()),
                }
            },
            default_flow_style=False,
            sort_keys=False,
        )

    @property
    def run_storage(self) -> "RunStorage":
        return self._run_storage

    @property
    def event_log_storage(self) -> "EventLogStorage":
        return self._event_storage

    # schedule storage

    @property
    def schedule_storage(self) -> Optional["ScheduleStorage"]:
        return self._schedule_storage

    @property
    def scheduler(self) -> Optional["Scheduler"]:
        return self._scheduler

    @property
    def scheduler_class(self) -> Optional[str]:
        return self.scheduler.__class__.__name__ if self.scheduler else None

    # run coordinator

    @property
    def run_coordinator(self) -> "RunCoordinator":
        return self._run_coordinator

    # run launcher

    @property
    def run_launcher(self) -> "RunLauncher":
        from dagster._core.launcher import RunLauncher

        # Lazily load in case the launcher requires dependencies that are not available everywhere
        # that loads the instance (e.g. The EcsRunLauncher requires boto3)
        if not self._run_launcher:
            check.invariant(self._ref, "Run launcher not provided, and no instance ref available")
            launcher = cast(InstanceRef, self._ref).run_launcher
            check.invariant(launcher, "Run launcher not configured in instance ref")
            self._run_launcher = cast(RunLauncher, launcher)
            self._run_launcher.register_instance(self)
        return self._run_launcher

    # compute logs

    @property
    def compute_log_manager(self) -> "ComputeLogManager":
        return self._compute_log_manager

    def get_settings(self, settings_key: str) -> Any:
        check.str_param(settings_key, "settings_key")
        if self._settings and settings_key in self._settings:
            return self._settings.get(settings_key)
        return {}

    @property
    def telemetry_enabled(self) -> bool:
        if self.is_ephemeral:
            return False

        dagster_telemetry_enabled_default = True

        telemetry_settings = self.get_settings("telemetry")

        if not telemetry_settings:
            return dagster_telemetry_enabled_default

        if "enabled" in telemetry_settings:
            return telemetry_settings["enabled"]
        else:
            return dagster_telemetry_enabled_default

    # run monitoring

    @property
    def run_monitoring_enabled(self) -> bool:
        return self._run_monitoring_enabled

    @property
    def run_monitoring_settings(self) -> Mapping:
        return self.get_settings("run_monitoring")

    @property
    def run_monitoring_start_timeout_seconds(self) -> int:
        return self.run_monitoring_settings.get("start_timeout_seconds", 180)

    @property
    def code_server_settings(self) -> Mapping:
        return self.get_settings("code_servers")

    @property
    def code_server_process_startup_timeout(self) -> int:
        return self.code_server_settings.get(
            "local_startup_timeout", DEFAULT_LOCAL_CODE_SERVER_STARTUP_TIMEOUT
        )

    @property
    def run_monitoring_max_resume_run_attempts(self) -> int:
        default_max_resume_run_attempts = 3 if self.run_launcher.supports_resume_run else 0
        return self.run_monitoring_settings.get(
            "max_resume_run_attempts", default_max_resume_run_attempts
        )

    @property
    def run_monitoring_poll_interval_seconds(self) -> int:
        return self.run_monitoring_settings.get("poll_interval_seconds", 120)

    @property
    def cancellation_thread_poll_interval_seconds(self) -> int:
        return self.get_settings("run_monitoring").get(
            "cancellation_thread_poll_interval_seconds", 10
        )

    @property
    def run_retries_enabled(self) -> bool:
        return self.get_settings("run_retries").get("enabled", False)

    @property
    def run_retries_max_retries(self) -> int:
        return self.get_settings("run_retries").get("max_retries")

    # python logs

    @property
    def managed_python_loggers(self) -> Sequence[str]:
        python_log_settings = self.get_settings("python_logs") or {}
        return python_log_settings.get("managed_python_loggers", [])

    @property
    def python_log_level(self) -> Optional[str]:
        python_log_settings = self.get_settings("python_logs") or {}
        return python_log_settings.get("python_log_level")

    def upgrade(self, print_fn=None):
        from dagster._core.storage.migration.utils import upgrading_instance

        with upgrading_instance(self):

            if print_fn:
                print_fn("Updating run storage...")
            self._run_storage.upgrade()
            self._run_storage.migrate(print_fn)

            if print_fn:
                print_fn("Updating event storage...")
            self._event_storage.upgrade()
            self._event_storage.reindex_assets(print_fn=print_fn)

            if print_fn:
                print_fn("Updating schedule storage...")
            self._schedule_storage.upgrade()
            self._schedule_storage.migrate(print_fn)

    def optimize_for_dagit(self, statement_timeout, pool_recycle):
        if self._schedule_storage:
            self._schedule_storage.optimize_for_dagit(
                statement_timeout=statement_timeout, pool_recycle=pool_recycle
            )
        self._run_storage.optimize_for_dagit(
            statement_timeout=statement_timeout, pool_recycle=pool_recycle
        )
        self._event_storage.optimize_for_dagit(
            statement_timeout=statement_timeout, pool_recycle=pool_recycle
        )

    def reindex(self, print_fn=lambda _: None):
        print_fn("Checking for reindexing...")
        self._event_storage.reindex_events(print_fn)
        self._event_storage.reindex_assets(print_fn)
        self._run_storage.optimize(print_fn)
        self._schedule_storage.optimize(print_fn)
        print_fn("Done.")

    def dispose(self):
        self._run_storage.dispose()
        self.run_coordinator.dispose()
        if self._run_launcher:
            self._run_launcher.dispose()
        self._event_storage.dispose()
        self._compute_log_manager.dispose()
        if self._secrets_loader:
            self._secrets_loader.dispose()

    # run storage
    @public
    @traced
    def get_run_by_id(self, run_id: str) -> Optional[DagsterRun]:
        return cast(DagsterRun, self._run_storage.get_run_by_id(run_id))

    @traced
    def get_pipeline_snapshot(self, snapshot_id: str) -> "PipelineSnapshot":
        return self._run_storage.get_pipeline_snapshot(snapshot_id)

    @traced
    def has_pipeline_snapshot(self, snapshot_id: str) -> bool:
        return self._run_storage.has_pipeline_snapshot(snapshot_id)

    @traced
    def has_snapshot(self, snapshot_id: str) -> bool:
        return self._run_storage.has_snapshot(snapshot_id)

    @traced
    def get_historical_pipeline(self, snapshot_id: str) -> "HistoricalPipeline":
        from dagster._core.host_representation import HistoricalPipeline

        snapshot = self._run_storage.get_pipeline_snapshot(snapshot_id)
        parent_snapshot = (
            self._run_storage.get_pipeline_snapshot(snapshot.lineage_snapshot.parent_snapshot_id)
            if snapshot.lineage_snapshot
            else None
        )
        return HistoricalPipeline(snapshot, snapshot_id, parent_snapshot)

    @traced
    def has_historical_pipeline(self, snapshot_id: str) -> bool:
        return self._run_storage.has_pipeline_snapshot(snapshot_id)

    @traced
    def get_execution_plan_snapshot(self, snapshot_id: str) -> "ExecutionPlanSnapshot":
        return self._run_storage.get_execution_plan_snapshot(snapshot_id)

    @traced
    def get_run_stats(self, run_id: str) -> PipelineRunStatsSnapshot:
        return self._event_storage.get_stats_for_run(run_id)

    @traced
    def get_run_step_stats(self, run_id, step_keys=None) -> Sequence["RunStepKeyStatsSnapshot"]:
        return self._event_storage.get_step_stats_for_run(run_id, step_keys)

    @traced
    def get_run_tags(self) -> Sequence[Tuple[str, Set[str]]]:
        return self._run_storage.get_run_tags()

    @traced
    def get_run_group(self, run_id: str) -> Optional[Tuple[str, Iterable[PipelineRun]]]:
        return self._run_storage.get_run_group(run_id)

    def create_run_for_pipeline(
        self,
        pipeline_def: PipelineDefinition,
        execution_plan: Optional["ExecutionPlan"] = None,
        run_id: Optional[str] = None,
        run_config: Optional[Mapping[str, object]] = None,
        mode: Optional[str] = None,
        solids_to_execute: Optional[AbstractSet[str]] = None,
        status: Optional[str] = None,
        tags: Optional[Mapping[str, str]] = None,
        root_run_id: Optional[str] = None,
        parent_run_id: Optional[str] = None,
        solid_selection: Optional[Sequence[str]] = None,
        asset_selection: Optional[FrozenSet[AssetKey]] = None,
        external_pipeline_origin=None,
        pipeline_code_origin=None,
        repository_load_data=None,
    ) -> PipelineRun:
        from dagster._core.definitions.job_definition import JobDefinition
        from dagster._core.execution.api import create_execution_plan
        from dagster._core.execution.plan.plan import ExecutionPlan
        from dagster._core.snap import snapshot_from_execution_plan

        check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
        check.opt_inst_param(execution_plan, "execution_plan", ExecutionPlan)

        # note that solids_to_execute is required to execute the solid subset, which is the
        # frozenset version of the previous solid_subset.
        # solid_selection is not required and will not be converted to solids_to_execute here.
        # i.e. this function doesn't handle solid queries.
        # solid_selection is only used to pass the user queries further down.
        check.opt_set_param(solids_to_execute, "solids_to_execute", of_type=str)
        check.opt_list_param(solid_selection, "solid_selection", of_type=str)
        check.opt_set_param(asset_selection, "asset_selection", of_type=AssetKey)

        if solids_to_execute:
            if isinstance(pipeline_def, PipelineSubsetDefinition):
                # for the case when pipeline_def is created by IPipeline or ExternalPipeline
                check.invariant(
                    solids_to_execute == pipeline_def.solids_to_execute,
                    "Cannot create a PipelineRun from pipeline subset {pipeline_solids_to_execute} "
                    "that conflicts with solids_to_execute arg {solids_to_execute}".format(
                        pipeline_solids_to_execute=str_format_list(pipeline_def.solids_to_execute),
                        solids_to_execute=str_format_list(solids_to_execute),
                    ),
                )
            else:
                # for cases when `create_run_for_pipeline` is directly called
                pipeline_def = pipeline_def.get_pipeline_subset_def(
                    solids_to_execute=solids_to_execute
                )
        if asset_selection and isinstance(pipeline_def, JobDefinition):
            # for cases when `create_run_for_pipeline` is directly called
            pipeline_def = pipeline_def.get_job_def_for_subset_selection(
                asset_selection=asset_selection
            )

        step_keys_to_execute = None

        if execution_plan:
            step_keys_to_execute = execution_plan.step_keys_to_execute

        else:
            execution_plan = create_execution_plan(
                pipeline=InMemoryPipeline(pipeline_def),
                run_config=run_config,
                mode=mode,
                instance_ref=self.get_ref() if self.is_persistent else None,
                tags=tags,
                repository_load_data=repository_load_data,
            )

        return self.create_run(
            pipeline_name=pipeline_def.name,
            run_id=run_id,
            run_config=run_config,
            mode=check.opt_str_param(mode, "mode", default=pipeline_def.get_default_mode_name()),
            solid_selection=solid_selection,
            asset_selection=asset_selection,
            solids_to_execute=solids_to_execute,
            step_keys_to_execute=step_keys_to_execute,
            status=status,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            pipeline_snapshot=pipeline_def.get_pipeline_snapshot(),
            execution_plan_snapshot=snapshot_from_execution_plan(
                execution_plan,
                pipeline_def.get_pipeline_snapshot_id(),
            ),
            parent_pipeline_snapshot=pipeline_def.get_parent_pipeline_snapshot(),
            external_pipeline_origin=external_pipeline_origin,
            pipeline_code_origin=pipeline_code_origin,
        )

    def _construct_run_with_snapshots(
        self,
        pipeline_name,
        run_id,
        run_config,
        mode,
        solids_to_execute,
        step_keys_to_execute,
        status,
        tags,
        root_run_id,
        parent_run_id,
        pipeline_snapshot,
        execution_plan_snapshot,
        parent_pipeline_snapshot,
        asset_selection=None,
        solid_selection=None,
        external_pipeline_origin=None,
        pipeline_code_origin=None,
    ) -> DagsterRun:

        # https://github.com/dagster-io/dagster/issues/2403
        if tags and IS_AIRFLOW_INGEST_PIPELINE_STR in tags:
            if AIRFLOW_EXECUTION_DATE_STR not in tags:
                tags[AIRFLOW_EXECUTION_DATE_STR] = get_current_datetime_in_utc().isoformat()

        check.invariant(
            not (not pipeline_snapshot and execution_plan_snapshot),
            "It is illegal to have an execution plan snapshot and not have a pipeline snapshot. "
            "It is possible to have no execution plan snapshot since we persist runs "
            "that do not successfully compile execution plans in the scheduled case.",
        )

        pipeline_snapshot_id = (
            self._ensure_persisted_pipeline_snapshot(pipeline_snapshot, parent_pipeline_snapshot)
            if pipeline_snapshot
            else None
        )

        execution_plan_snapshot_id = (
            self._ensure_persisted_execution_plan_snapshot(
                execution_plan_snapshot, pipeline_snapshot_id, step_keys_to_execute
            )
            if execution_plan_snapshot and pipeline_snapshot_id
            else None
        )

        return DagsterRun(
            pipeline_name=pipeline_name,
            run_id=run_id,
            run_config=run_config,
            mode=mode,
            asset_selection=asset_selection,
            solid_selection=solid_selection,
            solids_to_execute=solids_to_execute,
            step_keys_to_execute=step_keys_to_execute,
            status=status,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            pipeline_snapshot_id=pipeline_snapshot_id,
            execution_plan_snapshot_id=execution_plan_snapshot_id,
            external_pipeline_origin=external_pipeline_origin,
            pipeline_code_origin=pipeline_code_origin,
            has_repository_load_data=execution_plan_snapshot is not None
            and execution_plan_snapshot.repository_load_data is not None,
        )

    def _ensure_persisted_pipeline_snapshot(self, pipeline_snapshot, parent_pipeline_snapshot):
        from dagster._core.snap import PipelineSnapshot, create_pipeline_snapshot_id

        check.inst_param(pipeline_snapshot, "pipeline_snapshot", PipelineSnapshot)
        check.opt_inst_param(parent_pipeline_snapshot, "parent_pipeline_snapshot", PipelineSnapshot)

        if pipeline_snapshot.lineage_snapshot:
            if not self._run_storage.has_pipeline_snapshot(
                pipeline_snapshot.lineage_snapshot.parent_snapshot_id
            ):
                check.invariant(
                    create_pipeline_snapshot_id(parent_pipeline_snapshot)
                    == pipeline_snapshot.lineage_snapshot.parent_snapshot_id,
                    "Parent pipeline snapshot id out of sync with passed parent pipeline snapshot",
                )

                returned_pipeline_snapshot_id = self._run_storage.add_pipeline_snapshot(
                    parent_pipeline_snapshot
                )
                check.invariant(
                    pipeline_snapshot.lineage_snapshot.parent_snapshot_id
                    == returned_pipeline_snapshot_id
                )

        pipeline_snapshot_id = create_pipeline_snapshot_id(pipeline_snapshot)
        if not self._run_storage.has_pipeline_snapshot(pipeline_snapshot_id):
            returned_pipeline_snapshot_id = self._run_storage.add_pipeline_snapshot(
                pipeline_snapshot
            )
            check.invariant(pipeline_snapshot_id == returned_pipeline_snapshot_id)

        return pipeline_snapshot_id

    def _ensure_persisted_execution_plan_snapshot(
        self, execution_plan_snapshot, pipeline_snapshot_id, step_keys_to_execute
    ):
        from dagster._core.snap.execution_plan_snapshot import (
            ExecutionPlanSnapshot,
            create_execution_plan_snapshot_id,
        )

        check.inst_param(execution_plan_snapshot, "execution_plan_snapshot", ExecutionPlanSnapshot)
        check.str_param(pipeline_snapshot_id, "pipeline_snapshot_id")
        check.opt_nullable_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)

        check.invariant(
            execution_plan_snapshot.pipeline_snapshot_id == pipeline_snapshot_id,
            (
                "Snapshot mismatch: Snapshot ID in execution plan snapshot is "
                '"{ep_pipeline_snapshot_id}" and snapshot_id created in memory is '
                '"{pipeline_snapshot_id}"'
            ).format(
                ep_pipeline_snapshot_id=execution_plan_snapshot.pipeline_snapshot_id,
                pipeline_snapshot_id=pipeline_snapshot_id,
            ),
        )

        execution_plan_snapshot_id = create_execution_plan_snapshot_id(execution_plan_snapshot)

        if not self._run_storage.has_execution_plan_snapshot(execution_plan_snapshot_id):
            returned_execution_plan_snapshot_id = self._run_storage.add_execution_plan_snapshot(
                execution_plan_snapshot
            )

            check.invariant(execution_plan_snapshot_id == returned_execution_plan_snapshot_id)

        return execution_plan_snapshot_id

    def _log_asset_materialization_planned_events(self, pipeline_run, execution_plan_snapshot):
        from dagster._core.events import (
            AssetMaterializationPlannedData,
            DagsterEvent,
            DagsterEventType,
        )

        pipeline_name = pipeline_run.pipeline_name

        for step in execution_plan_snapshot.steps:
            if step.key in execution_plan_snapshot.step_keys_to_execute:
                for output in step.outputs:
                    asset_key = output.properties.asset_key
                    if asset_key:
                        # Logs and stores asset_materialization_planned event
                        event = DagsterEvent(
                            event_type_value=DagsterEventType.ASSET_MATERIALIZATION_PLANNED.value,
                            pipeline_name=pipeline_name,
                            message=f"{pipeline_name} intends to materialize asset {asset_key.to_string()}",
                            event_specific_data=AssetMaterializationPlannedData(asset_key),
                        )
                        self.report_dagster_event(event, pipeline_run.run_id, logging.DEBUG)

    def create_run(
        self,
        pipeline_name,
        run_id,
        run_config,
        mode,
        solids_to_execute,
        step_keys_to_execute,
        status,
        tags,
        root_run_id,
        parent_run_id,
        pipeline_snapshot,
        execution_plan_snapshot,
        parent_pipeline_snapshot,
        asset_selection=None,
        solid_selection=None,
        external_pipeline_origin=None,
        pipeline_code_origin=None,
    ) -> PipelineRun:

        pipeline_run = self._construct_run_with_snapshots(
            pipeline_name=pipeline_name,
            run_id=run_id,
            run_config=run_config,
            mode=mode,
            asset_selection=asset_selection,
            solid_selection=solid_selection,
            solids_to_execute=solids_to_execute,
            step_keys_to_execute=step_keys_to_execute,
            status=status,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            pipeline_snapshot=pipeline_snapshot,
            execution_plan_snapshot=execution_plan_snapshot,
            parent_pipeline_snapshot=parent_pipeline_snapshot,
            external_pipeline_origin=external_pipeline_origin,
            pipeline_code_origin=pipeline_code_origin,
        )

        pipeline_run = self._run_storage.add_run(pipeline_run)

        if execution_plan_snapshot:
            self._log_asset_materialization_planned_events(pipeline_run, execution_plan_snapshot)

        return pipeline_run

    def create_reexecuted_run(
        self,
        parent_run: DagsterRun,
        repo_location: "RepositoryLocation",
        external_pipeline: "ExternalPipeline",
        strategy: "ReexecutionStrategy",
        extra_tags: Optional[Mapping[str, Any]] = None,
        run_config: Optional[Mapping[str, Any]] = None,
        mode: Optional[str] = None,
        use_parent_run_tags: bool = False,
    ) -> PipelineRun:
        from dagster._core.execution.plan.resume_retry import (
            ReexecutionStrategy,
            get_retry_steps_from_parent_run,
        )
        from dagster._core.host_representation import ExternalPipeline, RepositoryLocation

        check.inst_param(parent_run, "parent_run", DagsterRun)
        check.inst_param(repo_location, "repo_location", RepositoryLocation)
        check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)
        check.inst_param(strategy, "strategy", ReexecutionStrategy)
        check.opt_mapping_param(extra_tags, "extra_tags", key_type=str)
        check.opt_mapping_param(run_config, "run_config", key_type=str)
        check.opt_str_param(mode, "mode")

        check.bool_param(use_parent_run_tags, "use_parent_run_tags")

        root_run_id = parent_run.root_run_id or parent_run.run_id
        parent_run_id = parent_run.run_id

        tags = merge_dicts(
            external_pipeline.tags,
            # these can differ from external_pipeline.tags if tags were added at launch time
            parent_run.tags if use_parent_run_tags else {},
            extra_tags or {},
            {
                PARENT_RUN_ID_TAG: parent_run_id,
                ROOT_RUN_ID_TAG: root_run_id,
            },
        )

        mode = cast(str, mode if mode is not None else parent_run.mode)
        run_config = run_config if run_config is not None else parent_run.run_config

        if strategy == ReexecutionStrategy.FROM_FAILURE:
            check.invariant(
                parent_run.status == PipelineRunStatus.FAILURE,
                "Cannot reexecute from failure a run that is not failed",
            )

            step_keys_to_execute, known_state = get_retry_steps_from_parent_run(
                self,
                parent_run=parent_run,
            )
            tags[RESUME_RETRY_TAG] = "true"
        elif strategy == ReexecutionStrategy.ALL_STEPS:
            step_keys_to_execute = None
            known_state = None
        else:
            raise DagsterInvariantViolationError(f"Unknown reexecution strategy: {strategy}")

        external_execution_plan = repo_location.get_external_execution_plan(
            external_pipeline,
            run_config,
            mode=mode,
            step_keys_to_execute=step_keys_to_execute,
            known_state=known_state,
            instance=self,
        )

        return self.create_run(
            pipeline_name=parent_run.pipeline_name,
            run_id=None,
            run_config=run_config,
            mode=mode,
            solids_to_execute=parent_run.solids_to_execute,
            step_keys_to_execute=step_keys_to_execute,
            status=PipelineRunStatus.NOT_STARTED,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            pipeline_snapshot=external_pipeline.pipeline_snapshot,
            execution_plan_snapshot=external_execution_plan.execution_plan_snapshot,
            parent_pipeline_snapshot=external_pipeline.parent_pipeline_snapshot,
            solid_selection=parent_run.solid_selection,
            asset_selection=parent_run.asset_selection,
            external_pipeline_origin=external_pipeline.get_external_origin(),
            pipeline_code_origin=external_pipeline.get_python_origin(),
        )

    def register_managed_run(
        self,
        pipeline_name,
        run_id,
        run_config,
        mode,
        solids_to_execute,
        step_keys_to_execute,
        tags,
        root_run_id,
        parent_run_id,
        pipeline_snapshot,
        execution_plan_snapshot,
        parent_pipeline_snapshot,
        solid_selection=None,
        pipeline_code_origin=None,
    ):
        # The usage of this method is limited to dagster-airflow, specifically in Dagster
        # Operators that are executed in Airflow. Because a common workflow in Airflow is to
        # retry dags from arbitrary tasks, we need any node to be capable of creating a
        # PipelineRun.
        #
        # The try-except DagsterRunAlreadyExists block handles the race when multiple "root" tasks
        # simultaneously execute self._run_storage.add_run(pipeline_run). When this happens, only
        # one task succeeds in creating the run, while the others get DagsterRunAlreadyExists
        # error; at this point, the failed tasks try again to fetch the existing run.
        # https://github.com/dagster-io/dagster/issues/2412

        pipeline_run = self._construct_run_with_snapshots(
            pipeline_name=pipeline_name,
            run_id=run_id,
            run_config=run_config,
            mode=mode,
            solid_selection=solid_selection,
            solids_to_execute=solids_to_execute,
            step_keys_to_execute=step_keys_to_execute,
            status=PipelineRunStatus.MANAGED,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            pipeline_snapshot=pipeline_snapshot,
            execution_plan_snapshot=execution_plan_snapshot,
            parent_pipeline_snapshot=parent_pipeline_snapshot,
            pipeline_code_origin=pipeline_code_origin,
        )

        def get_run():
            candidate_run = self.get_run_by_id(pipeline_run.run_id)

            field_diff = _check_run_equality(pipeline_run, candidate_run)

            if field_diff:
                raise DagsterRunConflict(
                    "Found conflicting existing run with same id {run_id}. Runs differ in:"
                    "\n{field_diff}".format(
                        run_id=pipeline_run.run_id,
                        field_diff=_format_field_diff(field_diff),
                    ),
                )
            return candidate_run

        if self.has_run(pipeline_run.run_id):
            return get_run()

        try:
            return self._run_storage.add_run(pipeline_run)
        except DagsterRunAlreadyExists:
            return get_run()

    @traced
    def add_run(self, pipeline_run: PipelineRun) -> PipelineRun:
        return self._run_storage.add_run(pipeline_run)

    @traced
    def add_snapshot(self, snapshot, snapshot_id=None):
        return self._run_storage.add_snapshot(snapshot, snapshot_id)

    @traced
    def handle_run_event(self, run_id: str, event: "DagsterEvent"):
        return self._run_storage.handle_run_event(run_id, event)

    @traced
    def add_run_tags(self, run_id: str, new_tags: Mapping[str, str]):
        return self._run_storage.add_run_tags(run_id, new_tags)

    @traced
    def has_run(self, run_id: str) -> bool:
        return self._run_storage.has_run(run_id)

    @traced
    def get_runs(
        self,
        filters: Optional[RunsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        bucket_by: Optional[Union[JobBucket, TagBucket]] = None,
    ) -> Iterable[PipelineRun]:
        return self._run_storage.get_runs(filters, cursor, limit, bucket_by)

    @traced
    def get_runs_count(self, filters: Optional[RunsFilter] = None) -> int:
        return self._run_storage.get_runs_count(filters)

    @traced
    def get_run_groups(
        self,
        filters: Optional[RunsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Mapping[str, Mapping[str, Union[Iterable[PipelineRun], int]]]:
        return self._run_storage.get_run_groups(filters=filters, cursor=cursor, limit=limit)

    @public
    @traced
    def get_run_records(
        self,
        filters: Optional[RunsFilter] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        ascending: bool = False,
        cursor: Optional[str] = None,
        bucket_by: Optional[Union[JobBucket, TagBucket]] = None,
    ) -> Sequence[RunRecord]:
        """Return a list of run records stored in the run storage, sorted by the given column in given order.

        Args:
            filters (Optional[RunsFilter]): the filter by which to filter runs.
            limit (Optional[int]): Number of results to get. Defaults to infinite.
            order_by (Optional[str]): Name of the column to sort by. Defaults to id.
            ascending (Optional[bool]): Sort the result in ascending order if True, descending
                otherwise. Defaults to descending.

        Returns:
            List[RunRecord]: List of run records stored in the run storage.
        """
        return self._run_storage.get_run_records(
            filters, limit, order_by, ascending, cursor, bucket_by
        )

    @property
    def supports_bucket_queries(self):
        return self._run_storage.supports_bucket_queries

    @traced
    def get_run_partition_data(self, runs_filter: RunsFilter) -> Sequence[RunPartitionData]:
        """Get run partition data for a given partitioned job."""
        return self._run_storage.get_run_partition_data(runs_filter)

    def wipe(self):
        self._run_storage.wipe()
        self._event_storage.wipe()

    @public
    @traced
    def delete_run(self, run_id: str):
        self._run_storage.delete_run(run_id)
        self._event_storage.delete_events(run_id)

    # event storage
    @traced
    def logs_after(
        self,
        run_id: str,
        cursor: Optional[int] = None,
        of_type: Optional["DagsterEventType"] = None,
        limit: Optional[int] = None,
    ):
        return self._event_storage.get_logs_for_run(
            run_id,
            cursor=cursor,
            of_type=of_type,
            limit=limit,
        )

    @traced
    def all_logs(
        self, run_id, of_type: Optional[Union["DagsterEventType", Set["DagsterEventType"]]] = None
    ):
        return self._event_storage.get_logs_for_run(run_id, of_type=of_type)

    @traced
    def get_records_for_run(
        self,
        run_id: str,
        cursor: Optional[str] = None,
        of_type: Optional[Union["DagsterEventType", Set["DagsterEventType"]]] = None,
        limit: Optional[int] = None,
    ):
        return self._event_storage.get_records_for_run(run_id, cursor, of_type, limit)

    def watch_event_logs(self, run_id, cursor, cb):
        return self._event_storage.watch(run_id, cursor, cb)

    def end_watch_event_logs(self, run_id, cb):
        return self._event_storage.end_watch(run_id, cb)

    # asset storage

    @traced
    def all_asset_keys(self):
        return self._event_storage.all_asset_keys()

    @public
    @traced
    def get_asset_keys(self, prefix=None, limit=None, cursor=None):
        return self._event_storage.get_asset_keys(prefix=prefix, limit=limit, cursor=cursor)

    @public
    @traced
    def has_asset_key(self, asset_key: AssetKey) -> bool:
        return self._event_storage.has_asset_key(asset_key)

    @traced
    def get_latest_materialization_events(
        self, asset_keys: Sequence[AssetKey]
    ) -> Mapping[AssetKey, Optional["EventLogEntry"]]:
        return self._event_storage.get_latest_materialization_events(asset_keys)

    @public
    @traced
    def get_latest_materialization_event(self, asset_key: AssetKey) -> Optional["EventLogEntry"]:
        return self._event_storage.get_latest_materialization_events([asset_key]).get(asset_key)

    @public
    @traced
    def get_event_records(
        self,
        event_records_filter: "EventRecordsFilter",
        limit: Optional[int] = None,
        ascending: bool = False,
    ) -> Iterable["EventLogRecord"]:
        """Return a list of event records stored in the event log storage.

        Args:
            event_records_filter (Optional[EventRecordsFilter]): the filter by which to filter event
                records.
            limit (Optional[int]): Number of results to get. Defaults to infinite.
            ascending (Optional[bool]): Sort the result in ascending order if True, descending
                otherwise. Defaults to descending.

        Returns:
            List[EventLogRecord]: List of event log records stored in the event log storage.
        """
        return self._event_storage.get_event_records(event_records_filter, limit, ascending)

    @public
    @traced
    def get_asset_records(
        self, asset_keys: Optional[Sequence[AssetKey]] = None
    ) -> Iterable["AssetRecord"]:
        return self._event_storage.get_asset_records(asset_keys)

    @traced
    def get_event_tags_for_asset(
        self,
        asset_key: AssetKey,
        filter_tags: Optional[Mapping[str, str]] = None,
        filter_event_id: Optional[int] = None,
    ) -> Sequence[Mapping[str, str]]:
        """
        Fetches asset event tags for the given asset key.

        If filter_tags is provided, searches for events containing all of the filter tags. Then,
        returns all tags for those events. This enables searching for multipartitioned asset
        partition tags with a fixed dimension value, e.g. all of the tags for events where
        "country" == "US".

        If filter_event_id is provided, searches for the event with the provided event_id.

        Returns a list of dicts, where each dict is a mapping of tag key to tag value for a
        single event.
        """
        return self._event_storage.get_event_tags_for_asset(asset_key, filter_tags, filter_event_id)

    @traced
    def run_ids_for_asset_key(self, asset_key):
        check.inst_param(asset_key, "asset_key", AssetKey)
        return self._event_storage.get_asset_run_ids(asset_key)

    @public
    @traced
    def wipe_assets(self, asset_keys: Sequence[AssetKey]):
        check.list_param(asset_keys, "asset_keys", of_type=AssetKey)
        for asset_key in asset_keys:
            self._event_storage.wipe_asset(asset_key)

    @traced
    def get_materialization_count_by_partition(
        self, asset_keys: Sequence[AssetKey]
    ) -> Mapping[AssetKey, Mapping[str, int]]:
        return self._event_storage.get_materialization_count_by_partition(asset_keys)

    # event subscriptions

    def _get_yaml_python_handlers(self):
        if self._settings:
            logging_config = self.get_settings("python_logs").get("dagster_handler_config", {})

            if logging_config:
                experimental_functionality_warning("Handling yaml-defined logging configuration")

            # Handlers can only be retrieved from dictConfig configuration if they are attached
            # to a logger. We add a dummy logger to the configuration that allows us to access user
            # defined handlers.
            handler_names = logging_config.get("handlers", {}).keys()

            dagster_dummy_logger_name = "dagster_dummy_logger"

            processed_dict_conf = {
                "version": 1,
                "disable_existing_loggers": False,
                "loggers": {dagster_dummy_logger_name: {"handlers": handler_names}},
            }
            processed_dict_conf.update(logging_config)

            logging.config.dictConfig(processed_dict_conf)

            dummy_logger = logging.getLogger(dagster_dummy_logger_name)
            return dummy_logger.handlers
        return []

    def _get_event_log_handler(self):
        event_log_handler = _EventListenerLogHandler(self)
        event_log_handler.setLevel(10)
        return event_log_handler

    def get_handlers(self):
        handlers = [self._get_event_log_handler()]
        handlers.extend(self._get_yaml_python_handlers())
        return handlers

    def store_event(self, event):
        self._event_storage.store_event(event)

    def handle_new_event(self, event):
        run_id = event.run_id

        self._event_storage.store_event(event)

        if event.is_dagster_event and event.dagster_event.is_pipeline_event:
            self._run_storage.handle_run_event(run_id, event.dagster_event)

        for sub in self._subscribers[run_id]:
            sub(event)

    def add_event_listener(self, run_id, cb):
        self._subscribers[run_id].append(cb)

    def report_engine_event(
        self,
        message,
        pipeline_run=None,
        engine_event_data=None,
        cls=None,
        step_key=None,
        pipeline_name=None,
        run_id=None,
    ):
        """
        Report a EngineEvent that occurred outside of a pipeline execution context.
        """
        from dagster._core.events import DagsterEvent, DagsterEventType, EngineEventData

        check.opt_class_param(cls, "cls")
        check.str_param(message, "message")
        check.opt_inst_param(pipeline_run, "pipeline_run", PipelineRun)
        check.opt_str_param(run_id, "run_id")
        check.opt_str_param(pipeline_name, "pipeline_name")

        check.invariant(
            pipeline_run or (pipeline_name and run_id),
            "Must include either pipeline_run or pipeline_name and run_id",
        )

        run_id = run_id if run_id else pipeline_run.run_id
        pipeline_name = pipeline_name if pipeline_name else pipeline_run.pipeline_name

        engine_event_data = check.opt_inst_param(
            engine_event_data,
            "engine_event_data",
            EngineEventData,
            EngineEventData([]),
        )

        if cls:
            message = "[{}] {}".format(cls.__name__, message)

        log_level = logging.INFO
        if engine_event_data and engine_event_data.error:
            log_level = logging.ERROR

        dagster_event = DagsterEvent(
            event_type_value=DagsterEventType.ENGINE_EVENT.value,
            pipeline_name=pipeline_name,
            message=message,
            event_specific_data=engine_event_data,
            step_key=step_key,
        )
        self.report_dagster_event(dagster_event, run_id=run_id, log_level=log_level)
        return dagster_event

    def report_dagster_event(
        self,
        dagster_event: "DagsterEvent",
        run_id: str,
        log_level: Union[str, int] = logging.INFO,
    ):
        """
        Takes a DagsterEvent and stores it in persistent storage for the corresponding PipelineRun
        """
        from dagster._core.events.log import EventLogEntry

        event_record = EventLogEntry(
            user_message="",
            level=log_level,
            pipeline_name=dagster_event.pipeline_name,
            run_id=run_id,
            error_info=None,
            timestamp=time.time(),
            step_key=dagster_event.step_key,
            dagster_event=dagster_event,
        )
        self.handle_new_event(event_record)

    def report_run_canceling(self, run, message=None):

        from dagster._core.events import DagsterEvent, DagsterEventType

        check.inst_param(run, "run", PipelineRun)
        message = check.opt_str_param(
            message,
            "message",
            "Sending run termination request.",
        )
        canceling_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_CANCELING.value,
            pipeline_name=run.pipeline_name,
            message=message,
        )
        self.report_dagster_event(canceling_event, run_id=run.run_id)

    def report_run_canceled(
        self,
        pipeline_run,
        message=None,
    ):
        from dagster._core.events import DagsterEvent, DagsterEventType

        check.inst_param(pipeline_run, "pipeline_run", PipelineRun)

        message = check.opt_str_param(
            message,
            "mesage",
            "This run has been marked as canceled from outside the execution context.",
        )

        dagster_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_CANCELED.value,
            pipeline_name=pipeline_run.pipeline_name,
            message=message,
        )
        self.report_dagster_event(
            dagster_event, run_id=pipeline_run.run_id, log_level=logging.ERROR
        )
        return dagster_event

    def report_run_failed(self, pipeline_run, message=None):
        from dagster._core.events import DagsterEvent, DagsterEventType

        check.inst_param(pipeline_run, "pipeline_run", PipelineRun)

        message = check.opt_str_param(
            message,
            "message",
            "This run has been marked as failed from outside the execution context.",
        )

        dagster_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
            pipeline_name=pipeline_run.pipeline_name,
            message=message,
        )
        self.report_dagster_event(
            dagster_event, run_id=pipeline_run.run_id, log_level=logging.ERROR
        )
        return dagster_event

    # directories

    def file_manager_directory(self, run_id: str):
        return self._local_artifact_storage.file_manager_dir(run_id)

    def storage_directory(self):
        return self._local_artifact_storage.storage_dir

    def schedules_directory(self):
        return self._local_artifact_storage.schedules_dir

    # Runs coordinator

    def submit_run(self, run_id, workspace: "IWorkspace") -> PipelineRun:
        """Submit a pipeline run to the coordinator.

        This method delegates to the ``RunCoordinator``, configured on the instance, and will
        call its implementation of ``RunCoordinator.submit_run()`` to send the run to the
        coordinator for execution. Runs should be created in the instance (e.g., by calling
        ``DagsterInstance.create_run()``) *before* this method is called, and
        should be in the ``PipelineRunStatus.NOT_STARTED`` state. They also must have a non-null
        ExternalPipelineOrigin.

        Args:
            run_id (str): The id of the run.
        """

        from dagster._core.host_representation import ExternalPipelineOrigin
        from dagster._core.origin import PipelinePythonOrigin
        from dagster._core.run_coordinator import SubmitRunContext

        run = self.get_run_by_id(run_id)
        if run is None:
            raise DagsterInvariantViolationError(
                f"Could not load run {run_id} that was passed to submit_run"
            )

        check.inst(
            run.external_pipeline_origin,
            ExternalPipelineOrigin,
            "External pipeline origin must be set for submitted runs",
        )
        check.inst(
            run.pipeline_code_origin,
            PipelinePythonOrigin,
            "Python origin must be set for submitted runs",
        )

        try:
            submitted_run = self._run_coordinator.submit_run(
                SubmitRunContext(run, workspace=workspace)
            )
        except:
            from dagster._core.events import EngineEventData

            error = serializable_error_info_from_exc_info(sys.exc_info())
            self.report_engine_event(
                error.message,
                run,
                EngineEventData.engine_error(error),
            )
            self.report_run_failed(run)
            raise

        return submitted_run

    # Run launcher

    def launch_run(self, run_id: str, workspace: "IWorkspace"):
        """Launch a pipeline run.

        This method is typically called using `instance.submit_run` rather than being invoked
        directly. This method delegates to the ``RunLauncher``, if any, configured on the instance,
        and will call its implementation of ``RunLauncher.launch_run()`` to begin the execution of
        the specified run. Runs should be created in the instance (e.g., by calling
        ``DagsterInstance.create_run()``) *before* this method is called, and should be in the
        ``PipelineRunStatus.NOT_STARTED`` state.

        Args:
            run_id (str): The id of the run the launch.
        """
        from dagster._core.events import DagsterEvent, DagsterEventType, EngineEventData
        from dagster._core.launcher import LaunchRunContext

        run = self.get_run_by_id(run_id)
        if run is None:
            raise DagsterInvariantViolationError(
                f"Could not load run {run_id} that was passed to launch_run"
            )

        launch_started_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_STARTING.value,
            pipeline_name=run.pipeline_name,
        )

        self.report_dagster_event(launch_started_event, run_id=run.run_id)

        run = self.get_run_by_id(run_id)
        if run is None:
            check.failed(f"Failed to reload run {run_id}")

        try:
            self.run_launcher.launch_run(LaunchRunContext(pipeline_run=run, workspace=workspace))
        except:
            error = serializable_error_info_from_exc_info(sys.exc_info())
            self.report_engine_event(
                error.message,
                run,
                EngineEventData.engine_error(error),
            )
            self.report_run_failed(run)
            raise

        return run

    def resume_run(self, run_id: str, workspace: "IWorkspace", attempt_number: int):
        """Resume a pipeline run.

        This method should be called on runs which have already been launched, but whose run workers
        have died.

        Args:
            run_id (str): The id of the run the launch.
        """
        from dagster._core.events import EngineEventData
        from dagster._core.launcher import ResumeRunContext
        from dagster._daemon.monitoring import RESUME_RUN_LOG_MESSAGE

        run = self.get_run_by_id(run_id)
        if run is None:
            raise DagsterInvariantViolationError(
                f"Could not load run {run_id} that was passed to resume_run"
            )
        if run.status not in IN_PROGRESS_RUN_STATUSES:
            raise DagsterInvariantViolationError(
                f"Run {run_id} is not in a state that can be resumed"
            )

        self.report_engine_event(
            RESUME_RUN_LOG_MESSAGE,
            run,
        )

        try:
            self.run_launcher.resume_run(
                ResumeRunContext(
                    pipeline_run=run,
                    workspace=workspace,
                    resume_attempt_number=attempt_number,
                )
            )
        except:
            error = serializable_error_info_from_exc_info(sys.exc_info())
            self.report_engine_event(
                error.message,
                run,
                EngineEventData.engine_error(error),
            )
            self.report_run_failed(run)
            raise

        return run

    def count_resume_run_attempts(self, run_id: str):
        from dagster._daemon.monitoring import count_resume_run_attempts

        return count_resume_run_attempts(self, run_id)

    def run_will_resume(self, run_id: str):
        if not self.run_monitoring_enabled:
            return False
        return self.count_resume_run_attempts(run_id) < self.run_monitoring_max_resume_run_attempts

    # Scheduler

    def start_schedule(self, external_schedule):
        return self._scheduler.start_schedule(self, external_schedule)

    def stop_schedule(self, schedule_origin_id, schedule_selector_id, external_schedule):
        return self._scheduler.stop_schedule(
            self, schedule_origin_id, schedule_selector_id, external_schedule
        )

    def scheduler_debug_info(self):
        from dagster._core.definitions.run_request import InstigatorType
        from dagster._core.scheduler import SchedulerDebugInfo

        errors = []

        schedules = []
        for schedule_state in self.all_instigator_state(instigator_type=InstigatorType.SCHEDULE):
            schedule_info = {
                schedule_state.instigator_name: {
                    "status": schedule_state.status.value,
                    "cron_schedule": schedule_state.instigator_data.cron_schedule,
                    "schedule_origin_id": schedule_state.instigator_origin_id,
                    "repository_origin_id": schedule_state.repository_origin_id,
                }
            }

            schedules.append(yaml.safe_dump(schedule_info, default_flow_style=False))

        return SchedulerDebugInfo(
            scheduler_config_info=self._info_str_for_component("Scheduler", self.scheduler),
            scheduler_info=self.scheduler.debug_info(),
            schedule_storage=schedules,
            errors=errors,
        )

    # Schedule / Sensor Storage

    def start_sensor(self, external_sensor: "ExternalSensor"):
        from dagster._core.definitions.run_request import InstigatorType
        from dagster._core.scheduler.instigation import (
            InstigatorState,
            InstigatorStatus,
            SensorInstigatorData,
        )

        stored_state = self.get_instigator_state(
            external_sensor.get_external_origin_id(), external_sensor.selector_id
        )

        computed_state = external_sensor.get_current_instigator_state(stored_state)
        if computed_state.is_running:
            return computed_state

        if not stored_state:
            return self.add_instigator_state(
                InstigatorState(
                    external_sensor.get_external_origin(),
                    InstigatorType.SENSOR,
                    InstigatorStatus.RUNNING,
                    SensorInstigatorData(min_interval=external_sensor.min_interval_seconds),
                )
            )
        else:
            return self.update_instigator_state(stored_state.with_status(InstigatorStatus.RUNNING))

    def stop_sensor(
        self,
        instigator_origin_id: str,
        selector_id: str,
        external_sensor: Optional["ExternalSensor"],
    ):
        from dagster._core.definitions.run_request import InstigatorType
        from dagster._core.scheduler.instigation import (
            InstigatorState,
            InstigatorStatus,
            SensorInstigatorData,
        )

        stored_state = self.get_instigator_state(instigator_origin_id, selector_id)
        computed_state: InstigatorState
        if external_sensor:
            computed_state = external_sensor.get_current_instigator_state(stored_state)
        else:
            computed_state = check.not_none(stored_state)

        if not computed_state.is_running:
            return computed_state

        if not stored_state:
            assert external_sensor
            return self.add_instigator_state(
                InstigatorState(
                    external_sensor.get_external_origin(),
                    InstigatorType.SENSOR,
                    InstigatorStatus.STOPPED,
                    SensorInstigatorData(min_interval=external_sensor.min_interval_seconds),
                )
            )
        else:
            return self.update_instigator_state(stored_state.with_status(InstigatorStatus.STOPPED))

    @traced
    def all_instigator_state(
        self, repository_origin_id=None, repository_selector_id=None, instigator_type=None
    ):
        if not self._schedule_storage:
            check.failed("Schedule storage not available")
        return self._schedule_storage.all_instigator_state(
            repository_origin_id, repository_selector_id, instigator_type
        )

    @traced
    def get_instigator_state(self, origin_id: str, selector_id: str) -> Optional["InstigatorState"]:
        if not self._schedule_storage:
            check.failed("Schedule storage not available")
        return self._schedule_storage.get_instigator_state(origin_id, selector_id)

    def add_instigator_state(self, state: "InstigatorState") -> "InstigatorState":
        if not self._schedule_storage:
            check.failed("Schedule storage not available")
        return self._schedule_storage.add_instigator_state(state)

    def update_instigator_state(self, state: "InstigatorState") -> "InstigatorState":
        if not self._schedule_storage:
            check.failed("Schedule storage not available")
        return self._schedule_storage.update_instigator_state(state)

    def delete_instigator_state(self, origin_id, selector_id):
        return self._schedule_storage.delete_instigator_state(origin_id, selector_id)

    @property
    def supports_batch_tick_queries(self):
        return self._schedule_storage and self._schedule_storage.supports_batch_queries

    @traced
    def get_batch_ticks(
        self,
        selector_ids: Sequence[str],
        limit: Optional[int] = None,
        statuses: Optional[Sequence["TickStatus"]] = None,
    ) -> Mapping[str, Iterable["InstigatorTick"]]:
        if not self._schedule_storage:
            return {}
        return self._schedule_storage.get_batch_ticks(selector_ids, limit, statuses)

    @traced
    def get_tick(self, origin_id, selector_id, timestamp):
        matches = self._schedule_storage.get_ticks(
            origin_id, selector_id, before=timestamp + 1, after=timestamp - 1, limit=1
        )
        return matches[0] if len(matches) else None

    @traced
    def get_ticks(self, origin_id, selector_id, before=None, after=None, limit=None, statuses=None):
        return self._schedule_storage.get_ticks(
            origin_id, selector_id, before=before, after=after, limit=limit, statuses=statuses
        )

    def create_tick(self, tick_data: "TickData") -> "InstigatorTick":
        return check.not_none(self._schedule_storage).create_tick(tick_data)

    def update_tick(self, tick: "InstigatorTick"):
        return check.not_none(self._schedule_storage).update_tick(tick)

    def purge_ticks(self, origin_id, selector_id, before, tick_statuses=None):
        self._schedule_storage.purge_ticks(origin_id, selector_id, before, tick_statuses)

    def wipe_all_schedules(self):
        if self._scheduler:
            self._scheduler.wipe(self)

        self._schedule_storage.wipe()

    def logs_path_for_schedule(self, schedule_origin_id):
        return self._scheduler.get_logs_path(self, schedule_origin_id)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.dispose()
        if DagsterInstance._EXIT_STACK:
            DagsterInstance._EXIT_STACK.close()

    # dagster daemon
    def add_daemon_heartbeat(self, daemon_heartbeat: "DaemonHeartbeat"):
        """Called on a regular interval by the daemon"""
        self._run_storage.add_daemon_heartbeat(daemon_heartbeat)

    def get_daemon_heartbeats(self) -> Mapping[str, "DaemonHeartbeat"]:
        """Latest heartbeats of all daemon types"""
        return self._run_storage.get_daemon_heartbeats()

    def wipe_daemon_heartbeats(self):
        self._run_storage.wipe_daemon_heartbeats()

    def get_required_daemon_types(self):
        from dagster._core.run_coordinator import QueuedRunCoordinator
        from dagster._core.scheduler import DagsterDaemonScheduler
        from dagster._daemon.auto_run_reexecution.event_log_consumer import EventLogConsumerDaemon
        from dagster._daemon.daemon import (
            BackfillDaemon,
            MonitoringDaemon,
            SchedulerDaemon,
            SensorDaemon,
        )
        from dagster._daemon.run_coordinator.queued_run_coordinator_daemon import (
            QueuedRunCoordinatorDaemon,
        )

        if self.is_ephemeral:
            return []

        daemons = [SensorDaemon.daemon_type(), BackfillDaemon.daemon_type()]
        if isinstance(self.scheduler, DagsterDaemonScheduler):
            daemons.append(SchedulerDaemon.daemon_type())
        if isinstance(self.run_coordinator, QueuedRunCoordinator):
            daemons.append(QueuedRunCoordinatorDaemon.daemon_type())
        if self.run_monitoring_enabled:
            daemons.append(MonitoringDaemon.daemon_type())
        if self.run_retries_enabled:
            daemons.append(EventLogConsumerDaemon.daemon_type())
        return daemons

    def get_daemon_statuses(
        self, daemon_types: Optional[Sequence[str]] = None
    ) -> Mapping[str, "DaemonStatus"]:
        """
        Get the current status of the daemons. If daemon_types aren't provided, defaults to all
        required types. Returns a dict of daemon type to status.
        """
        from dagster._daemon.controller import get_daemon_statuses

        check.opt_sequence_param(daemon_types, "daemon_types", of_type=str)
        return get_daemon_statuses(
            self, daemon_types=daemon_types or self.get_required_daemon_types(), ignore_errors=True
        )

    @property
    def daemon_skip_heartbeats_without_errors(self):
        # If enabled, daemon threads won't write heartbeats unless they encounter an error. This is
        # enabled in cloud, where we don't need to use heartbeats to check if daemons are running, but
        # do need to surface errors to users. This is an optimization to reduce DB writes.
        return False

    # backfill
    def get_backfills(self, status=None, cursor=None, limit=None) -> Sequence["PartitionBackfill"]:
        return self._run_storage.get_backfills(status=status, cursor=cursor, limit=limit)

    def get_backfill(self, backfill_id: str) -> Optional["PartitionBackfill"]:
        return self._run_storage.get_backfill(backfill_id)

    def add_backfill(self, partition_backfill: "PartitionBackfill") -> None:
        self._run_storage.add_backfill(partition_backfill)

    def update_backfill(self, partition_backfill: "PartitionBackfill") -> None:
        self._run_storage.update_backfill(partition_backfill)

    @property
    def should_start_background_run_thread(self) -> bool:
        """
        Gate on an experimental feature to start a thread that monitors for if the run should be canceled.
        """
        return False

    def get_tick_retention_settings(
        self, instigator_type: "InstigatorType"
    ) -> Mapping["TickStatus", int]:
        from dagster._core.definitions.run_request import InstigatorType

        retention_settings = self.get_settings("retention")
        tick_settings = (
            retention_settings.get("schedule")
            if instigator_type == InstigatorType.SCHEDULE
            else retention_settings.get("sensor")
        )
        default_tick_settings = get_default_tick_retention_settings(instigator_type)
        return get_tick_retention_settings(tick_settings, default_tick_settings)

    def inject_env_vars(self, location_name: Optional[str]):
        if not self._secrets_loader:
            return

        new_env = self._secrets_loader.get_secrets_for_environment(location_name)
        for k, v in new_env.items():
            os.environ[k] = v

    def get_latest_logical_version_record(
        self,
        key: AssetKey,
        is_source: Optional[bool] = None,
    ) -> Optional[EventLogRecord]:
        from dagster._core.event_api import EventRecordsFilter
        from dagster._core.events import DagsterEventType

        # When we cant don't know whether the requested key corresponds to a source or regular
        # asset, we need to retrieve both the latest observation and materialization for all assets.
        # If there is a materialization, it's a regular asset and we can ignore the observation.

        observation: Optional[EventLogRecord] = None
        if is_source or is_source is None:
            observations = self.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_OBSERVATION,
                    asset_key=key,
                ),
                limit=1,
            )
            observation = next(iter(observations), None)

        materialization: Optional[EventLogRecord] = None
        if not is_source:
            materializations = self.get_event_records(
                EventRecordsFilter(
                    event_type=DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=key,
                ),
                limit=1,
            )
            materialization = next(iter(materializations), None)

        return materialization or observation
