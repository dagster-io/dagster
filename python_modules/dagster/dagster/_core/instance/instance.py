import logging
import logging.config
import os
import sys
import warnings
import weakref
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from functools import cached_property
from tempfile import TemporaryDirectory
from types import TracebackType
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Dict,  # noqa: F401
    List,  # noqa: F401
    Optional,
    Set,  # noqa: F401
    Tuple,  # noqa: F401
    Type,  # noqa: F401
    Union,
    cast,
)

import yaml
from typing_extensions import Self, TypeAlias

import dagster._check as check
from dagster._annotations import deprecated, public
from dagster._core.definitions.events import AssetKey, AssetObservation
from dagster._core.definitions.freshness import (
    FreshnessStateChange,
    FreshnessStateEvaluation,
    FreshnessStateRecord,
)
from dagster._core.errors import (
    DagsterHomeNotSetError,
    DagsterInvalidInvocationError,
    DagsterInvariantViolationError,
)
from dagster._core.instance.config import (
    DAGSTER_CONFIG_YAML_FILENAME,
    DEFAULT_LOCAL_CODE_SERVER_STARTUP_TIMEOUT,
    ConcurrencyConfig,
    get_default_tick_retention_settings,
    get_tick_retention_settings,
)
from dagster._core.instance.ref import InstanceRef
from dagster._core.instance.types import (
    DynamicPartitionsStore,
    InstanceType,
    _EventListenerLogHandler,
)
from dagster._core.origin import JobPythonOrigin
from dagster._core.storage.dagster_run import (
    IN_PROGRESS_RUN_STATUSES,
    DagsterRun,
    DagsterRunStatsSnapshot,
    DagsterRunStatus,
    JobBucket,
    RunPartitionData,
    RunRecord,
    RunsFilter,
    TagBucket,
)
from dagster._core.types.pagination import PaginatedResults
from dagster._serdes import ConfigurableClass
from dagster._time import get_current_timestamp
from dagster._utils import PrintFn, traced
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.warnings import beta_warning

if TYPE_CHECKING:
    from dagster._core.debug import DebugRunPayload
    from dagster._core.definitions.asset_checks.asset_check_evaluation import AssetCheckEvaluation
    from dagster._core.definitions.asset_checks.asset_check_spec import AssetCheckKey
    from dagster._core.definitions.asset_health.asset_check_health import AssetCheckHealthState
    from dagster._core.definitions.asset_health.asset_freshness_health import (
        AssetFreshnessHealthState,
    )
    from dagster._core.definitions.asset_health.asset_materialization_health import (
        AssetMaterializationHealthState,
        MinimalAssetMaterializationHealthState,
    )
    from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph
    from dagster._core.definitions.job_definition import JobDefinition
    from dagster._core.definitions.partitions.definition import PartitionsDefinition
    from dagster._core.definitions.repository_definition.repository_definition import (
        RepositoryLoadData,
    )
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.event_api import (
        AssetRecordsFilter,
        EventHandlerFn,
        RunStatusChangeRecordsFilter,
    )
    from dagster._core.events import (
        AssetMaterialization,
        DagsterEvent,
        DagsterEventBatchMetadata,
        DagsterEventType,
        EngineEventData,
        JobFailureData,
    )
    from dagster._core.events.log import EventLogEntry
    from dagster._core.execution.backfill import (
        BulkActionsFilter,
        BulkActionStatus,
        PartitionBackfill,
    )
    from dagster._core.execution.plan.plan import ExecutionPlan
    from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
    from dagster._core.execution.stats import RunStepKeyStatsSnapshot
    from dagster._core.launcher import RunLauncher
    from dagster._core.remote_representation import (
        CodeLocation,
        HistoricalJob,
        RemoteJob,
        RemoteJobOrigin,
        RemoteSensor,
    )
    from dagster._core.remote_representation.external import RemoteSchedule
    from dagster._core.run_coordinator import RunCoordinator
    from dagster._core.scheduler import Scheduler, SchedulerDebugInfo
    from dagster._core.scheduler.instigation import (
        InstigatorState,
        InstigatorStatus,
        InstigatorTick,
        TickData,
        TickStatus,
    )
    from dagster._core.secrets import SecretsLoader
    from dagster._core.snap import ExecutionPlanSnapshot, JobSnap
    from dagster._core.storage.asset_check_execution_record import (
        AssetCheckExecutionRecord,
        AssetCheckInstanceSupport,
    )
    from dagster._core.storage.compute_log_manager import ComputeLogManager
    from dagster._core.storage.daemon_cursor import DaemonCursorStorage
    from dagster._core.storage.event_log import EventLogStorage
    from dagster._core.storage.event_log.base import (
        AssetRecord,
        EventLogConnection,
        EventLogRecord,
        EventRecordsFilter,
        EventRecordsResult,
        PlannedMaterializationInfo,
    )
    from dagster._core.storage.partition_status_cache import (
        AssetPartitionStatus,
        AssetStatusCacheValue,
    )
    from dagster._core.storage.root import LocalArtifactStorage
    from dagster._core.storage.runs import RunStorage
    from dagster._core.storage.schedules import ScheduleStorage
    from dagster._core.storage.sql import AlembicVersion
    from dagster._core.workspace.context import BaseWorkspaceRequestContext
    from dagster._daemon.types import DaemonHeartbeat, DaemonStatus

DagsterInstanceOverrides: TypeAlias = Mapping[str, Any]


@public
class DagsterInstance(DynamicPartitionsStore):
    """Core abstraction for managing Dagster's access to storage and other resources.

    Use DagsterInstance.get() to grab the current DagsterInstance which will load based on
    the values in the ``dagster.yaml`` file in ``$DAGSTER_HOME``.

    Alternatively, DagsterInstance.ephemeral() can use used which provides a set of
    transient in-memory components.

    Configuration of this class should be done by setting values in ``$DAGSTER_HOME/dagster.yaml``.
    For example, to use Postgres for dagster storage, you can write a ``dagster.yaml`` such as the
    following:

    .. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/deploying/dagster-pg.yaml
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
        compute_log_manager (Optional[ComputeLogManager]): The compute log manager handles stdout
            and stderr logging for op compute functions. By default, this will be a
            :py:class:`dagster._core.storage.local_compute_log_manager.LocalComputeLogManager`.
            Configurable in ``dagster.yaml`` using the
            :py:class:`~dagster.serdes.ConfigurableClass` machinery.
        run_coordinator (Optional[RunCoordinator]): A runs coordinator may be used to manage the execution
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

    # Stores TemporaryDirectory instances that were created for DagsterInstance.local_temp() calls
    # to be removed once the instance is garbage collected.
    _TEMP_DIRS: "weakref.WeakKeyDictionary[DagsterInstance, TemporaryDirectory]" = (
        weakref.WeakKeyDictionary()
    )

    def __init__(
        self,
        instance_type: InstanceType,
        local_artifact_storage: "LocalArtifactStorage",
        run_storage: "RunStorage",
        event_storage: "EventLogStorage",
        run_coordinator: Optional["RunCoordinator"],
        compute_log_manager: Optional["ComputeLogManager"],
        run_launcher: Optional["RunLauncher"],
        scheduler: Optional["Scheduler"] = None,
        schedule_storage: Optional["ScheduleStorage"] = None,
        settings: Optional[Mapping[str, Any]] = None,
        secrets_loader: Optional["SecretsLoader"] = None,
        ref: Optional[InstanceRef] = None,
        **_kwargs: Any,  # we accept kwargs for forward-compat of custom instances
    ):
        from dagster._core.launcher import RunLauncher
        from dagster._core.run_coordinator import RunCoordinator
        from dagster._core.scheduler import Scheduler
        from dagster._core.secrets import SecretsLoader
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

        if compute_log_manager:
            self._compute_log_manager = check.inst_param(
                compute_log_manager, "compute_log_manager", ComputeLogManager
            )
            self._compute_log_manager.register_instance(self)
        else:
            check.invariant(
                ref,
                "Compute log manager must be provided if instance is not from a ref",
            )
            self._compute_log_manager = None

        self._scheduler = check.opt_inst_param(scheduler, "scheduler", Scheduler)

        self._schedule_storage = check.opt_inst_param(
            schedule_storage, "schedule_storage", ScheduleStorage
        )
        if self._schedule_storage:
            self._schedule_storage.register_instance(self)

        if run_coordinator:
            self._run_coordinator = check.inst_param(
                run_coordinator, "run_coordinator", RunCoordinator
            )
            self._run_coordinator.register_instance(self)
        else:
            check.invariant(ref, "Run coordinator must be provided if instance is not from a ref")
            self._run_coordinator = None

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

        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

        run_monitoring_enabled = self.run_monitoring_settings.get("enabled", False)
        self._run_monitoring_enabled = run_monitoring_enabled
        if self.run_monitoring_enabled and self.run_monitoring_max_resume_run_attempts:
            check.invariant(
                self.run_launcher.supports_resume_run,
                "The configured run launcher does not support resuming runs. Set"
                " max_resume_run_attempts to 0 to use run monitoring. Any runs with a failed"
                " run worker will be marked as failed, but will not be resumed.",
            )

        # Used for batched event handling
        self._event_buffer: dict[str, list[EventLogEntry]] = defaultdict(list)

    # ctors

    @public
    @staticmethod
    def ephemeral(
        tempdir: Optional[str] = None,
        preload: Optional[Sequence["DebugRunPayload"]] = None,
        settings: Optional[dict] = None,
    ) -> "DagsterInstance":
        """Create a `DagsterInstance` suitable for ephemeral execution, useful in test contexts. An
        ephemeral instance uses mostly in-memory components. Use `local_temp` to create a test
        instance that is fully persistent.

        Args:
            tempdir (Optional[str]): The path of a directory to be used for local artifact storage.
            preload (Optional[Sequence[DebugRunPayload]]): A sequence of payloads to load into the
                instance's run storage. Useful for debugging.
            settings (Optional[Dict]): Settings for the instance.

        Returns:
            DagsterInstance: An ephemeral DagsterInstance.
        """
        from dagster._core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
        from dagster._core.run_coordinator import DefaultRunCoordinator
        from dagster._core.storage.event_log import InMemoryEventLogStorage
        from dagster._core.storage.noop_compute_log_manager import NoOpComputeLogManager
        from dagster._core.storage.root import LocalArtifactStorage, TemporaryLocalArtifactStorage
        from dagster._core.storage.runs import InMemoryRunStorage

        if tempdir is not None:
            local_storage = LocalArtifactStorage(tempdir)
        else:
            local_storage = TemporaryLocalArtifactStorage()

        return DagsterInstance(
            instance_type=InstanceType.EPHEMERAL,
            local_artifact_storage=local_storage,
            run_storage=InMemoryRunStorage(preload=preload),
            event_storage=InMemoryEventLogStorage(preload=preload),
            compute_log_manager=NoOpComputeLogManager(),
            run_coordinator=DefaultRunCoordinator(),
            run_launcher=SyncInMemoryRunLauncher(),
            settings=settings,
        )

    @public
    @staticmethod
    def get() -> "DagsterInstance":
        """Get the current `DagsterInstance` as specified by the ``DAGSTER_HOME`` environment variable.

        Returns:
            DagsterInstance: The current DagsterInstance.
        """
        dagster_home_path = os.getenv("DAGSTER_HOME")

        if not dagster_home_path:
            raise DagsterHomeNotSetError(
                "The environment variable $DAGSTER_HOME is not set. \nDagster requires this"
                " environment variable to be set to an existing directory in your filesystem. This"
                " directory is used to store metadata across sessions, or load the dagster.yaml"
                " file which can configure storing metadata in an external database.\nYou can"
                " resolve this error by exporting the environment variable. For example, you can"
                " run the following command in your shell or include it in your shell configuration"
                ' file:\n\texport DAGSTER_HOME=~"/dagster_home"\nor PowerShell\n$env:DAGSTER_HOME'
                " = ($home + '\\dagster_home')or batchset"
                " DAGSTER_HOME=%UserProfile%/dagster_homeAlternatively, DagsterInstance.ephemeral()"
                " can be used for a transient instance.\n"
            )

        dagster_home_path = os.path.expanduser(dagster_home_path)

        if not os.path.isabs(dagster_home_path):
            raise DagsterInvariantViolationError(
                f'$DAGSTER_HOME "{dagster_home_path}" must be an absolute path. Dagster requires this '
                "environment variable to be set to an existing directory in your filesystem."
            )

        if not (os.path.exists(dagster_home_path) and os.path.isdir(dagster_home_path)):
            raise DagsterInvariantViolationError(
                f'$DAGSTER_HOME "{dagster_home_path}" is not a directory or does not exist. Dagster requires this'
                " environment variable to be set to an existing directory in your filesystem"
            )

        return DagsterInstance.from_config(dagster_home_path)

    @public
    @staticmethod
    def local_temp(
        tempdir: Optional[str] = None,
        overrides: Optional[DagsterInstanceOverrides] = None,
    ) -> "DagsterInstance":
        """Create a DagsterInstance that uses a temporary directory for local storage. This is a
        regular, fully persistent instance. Use `ephemeral` to get an ephemeral instance with
        in-memory components.

        Args:
            tempdir (Optional[str]): The path of a directory to be used for local artifact storage.
            overrides (Optional[DagsterInstanceOverrides]): Override settings for the instance.

        Returns:
            DagsterInstance
        """
        if tempdir is None:
            created_dir = TemporaryDirectory()
            i = DagsterInstance.from_ref(
                InstanceRef.from_dir(created_dir.name, overrides=overrides)
            )
            DagsterInstance._TEMP_DIRS[i] = created_dir
            return i

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

        return klass(
            instance_type=InstanceType.PERSISTENT,
            local_artifact_storage=instance_ref.local_artifact_storage,
            run_storage=run_storage,  # type: ignore  # (possible none)
            event_storage=event_storage,  # type: ignore  # (possible none)
            schedule_storage=schedule_storage,
            compute_log_manager=None,  # lazy load
            scheduler=instance_ref.scheduler,
            run_coordinator=None,  # lazy load
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
                dagster_home_msg=(
                    "\nDAGSTER_HOME environment variable is not set, set it to "
                    "a directory on the filesystem for dagster to use for storage and cross "
                    "process coordination."
                    if os.getenv("DAGSTER_HOME") is None
                    else ""
                ),
            )
        )

    @property
    def root_directory(self) -> str:
        return self._local_artifact_storage.base_dir

    def _info(self, component: object) -> Union[str, Mapping[Any, Any]]:
        # ConfigurableClass may not have inst_data if it's a direct instantiation
        # which happens for ephemeral instances
        if isinstance(component, ConfigurableClass) and component.inst_data:
            return component.inst_data.info_dict()
        if type(component) is dict:
            return component
        return component.__class__.__name__

    def _info_str_for_component(self, component_name: str, component: object) -> str:
        return yaml.dump(
            {component_name: self._info(component)},
            default_flow_style=False,
            sort_keys=False,
        )

    def info_dict(self) -> Mapping[str, object]:
        settings: Mapping[str, object] = self._settings if self._settings else {}

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
        def _schema_dict(
            alembic_version: "AlembicVersion",
        ) -> Optional[Mapping[str, object]]:
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
                    "event_log_storage": _schema_dict(self._event_storage.alembic_version()),  # type: ignore  # (possible none)
                    "run_storage": _schema_dict(self._event_storage.alembic_version()),  # type: ignore  # (possible none)
                    "schedule_storage": _schema_dict(self._event_storage.alembic_version()),  # type: ignore  # (possible none)
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

    @property
    def daemon_cursor_storage(self) -> "DaemonCursorStorage":
        return self._run_storage

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
        # Lazily load in case the run coordinator requires dependencies that are not available
        # everywhere that loads the instance
        if not self._run_coordinator:
            check.invariant(
                self._ref, "Run coordinator not provided, and no instance ref available"
            )
            run_coordinator = cast("InstanceRef", self._ref).run_coordinator
            check.invariant(run_coordinator, "Run coordinator not configured in instance ref")
            self._run_coordinator = cast("RunCoordinator", run_coordinator)
            self._run_coordinator.register_instance(self)
        return self._run_coordinator

    def get_concurrency_config(self) -> ConcurrencyConfig:
        from dagster._core.run_coordinator.queued_run_coordinator import QueuedRunCoordinator

        if isinstance(self.run_coordinator, QueuedRunCoordinator):
            run_coordinator_run_queue_config = self.run_coordinator.get_run_queue_config()
        else:
            run_coordinator_run_queue_config = None

        concurrency_settings = self.get_settings("concurrency")
        return ConcurrencyConfig.from_concurrency_settings(
            concurrency_settings, run_coordinator_run_queue_config
        )

    @property
    def run_launcher(self) -> "RunLauncher":
        # Lazily load in case the launcher requires dependencies that are not available everywhere
        # that loads the instance (e.g. The EcsRunLauncher requires boto3)
        if not self._run_launcher:
            check.invariant(self._ref, "Run launcher not provided, and no instance ref available")
            launcher = cast("InstanceRef", self._ref).run_launcher
            check.invariant(launcher, "Run launcher not configured in instance ref")
            self._run_launcher = cast("RunLauncher", launcher)
            self._run_launcher.register_instance(self)
        return self._run_launcher

    # compute logs

    @property
    def compute_log_manager(self) -> "ComputeLogManager":
        if not self._compute_log_manager:
            check.invariant(
                self._ref,
                "Compute log manager not provided, and no instance ref available",
            )
            compute_log_manager = cast("InstanceRef", self._ref).compute_log_manager
            check.invariant(
                compute_log_manager,
                "Compute log manager not configured in instance ref",
            )
            self._compute_log_manager = cast("ComputeLogManager", compute_log_manager)
            self._compute_log_manager.register_instance(self)
        return self._compute_log_manager

    def get_settings(self, settings_key: str) -> Any:
        check.str_param(settings_key, "settings_key")
        if self._settings and settings_key in self._settings:
            return self._settings.get(settings_key)
        return {}

    def get_backfill_settings(self) -> Mapping[str, Any]:
        return self.get_settings("backfills")

    def get_scheduler_settings(self) -> Mapping[str, Any]:
        return self.get_settings("schedules")

    def get_sensor_settings(self) -> Mapping[str, Any]:
        return self.get_settings("sensors")

    def get_auto_materialize_settings(self) -> Mapping[str, Any]:
        return self.get_settings("auto_materialize")

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

    @property
    def nux_enabled(self) -> bool:
        if self.is_ephemeral:
            return False

        nux_enabled_by_default = True

        nux_settings = self.get_settings("nux")
        if not nux_settings:
            return nux_enabled_by_default

        if "enabled" in nux_settings:
            return nux_settings["enabled"]
        else:
            return nux_enabled_by_default

    # run monitoring

    @property
    def run_monitoring_enabled(self) -> bool:
        return self._run_monitoring_enabled

    @property
    def run_monitoring_settings(self) -> Any:
        return self.get_settings("run_monitoring")

    @property
    def run_monitoring_start_timeout_seconds(self) -> int:
        return self.run_monitoring_settings.get("start_timeout_seconds", 180)

    @property
    def run_monitoring_cancel_timeout_seconds(self) -> int:
        return self.run_monitoring_settings.get("cancel_timeout_seconds", 180)

    @property
    def run_monitoring_max_runtime_seconds(self) -> int:
        return self.run_monitoring_settings.get("max_runtime_seconds", 0)

    @property
    def code_server_settings(self) -> Any:
        return self.get_settings("code_servers")

    @property
    def code_server_process_startup_timeout(self) -> int:
        return self.code_server_settings.get(
            "local_startup_timeout", DEFAULT_LOCAL_CODE_SERVER_STARTUP_TIMEOUT
        )

    @property
    def code_server_reload_timeout(self) -> int:
        return self.code_server_settings.get(
            "reload_timeout", DEFAULT_LOCAL_CODE_SERVER_STARTUP_TIMEOUT
        )

    @property
    def wait_for_local_code_server_processes_on_shutdown(self) -> bool:
        return self.code_server_settings.get("wait_for_local_processes_on_shutdown", False)

    @property
    def run_monitoring_max_resume_run_attempts(self) -> int:
        return self.run_monitoring_settings.get("max_resume_run_attempts", 0)

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
        return self.get_settings("run_retries").get("max_retries", 0)

    @property
    def run_retries_retry_on_asset_or_op_failure(self) -> bool:
        return self.get_settings("run_retries").get("retry_on_asset_or_op_failure", True)

    @property
    def auto_materialize_enabled(self) -> bool:
        return self.get_settings("auto_materialize").get("enabled", True)

    @property
    def freshness_enabled(self) -> bool:
        return self.get_settings("freshness").get("enabled", False)

    @property
    def auto_materialize_minimum_interval_seconds(self) -> int:
        return self.get_settings("auto_materialize").get("minimum_interval_seconds")

    @property
    def auto_materialize_run_tags(self) -> dict[str, str]:
        return self.get_settings("auto_materialize").get("run_tags", {})

    @property
    def auto_materialize_respect_materialization_data_versions(self) -> bool:
        return self.get_settings("auto_materialize").get(
            "respect_materialization_data_versions", False
        )

    @property
    def auto_materialize_max_tick_retries(self) -> int:
        return self.get_settings("auto_materialize").get("max_tick_retries", 3)

    @property
    def auto_materialize_use_sensors(self) -> bool:
        return self.get_settings("auto_materialize").get("use_sensors", True)

    @property
    def global_op_concurrency_default_limit(self) -> Optional[int]:
        return self.get_concurrency_config().pool_config.default_pool_limit

    # python logs

    @property
    def managed_python_loggers(self) -> Sequence[str]:
        python_log_settings = self.get_settings("python_logs") or {}
        loggers: Sequence[str] = python_log_settings.get("managed_python_loggers", [])
        return loggers

    @property
    def python_log_level(self) -> Optional[str]:
        python_log_settings = self.get_settings("python_logs") or {}
        return python_log_settings.get("python_log_level")

    def upgrade(self, print_fn: Optional[PrintFn] = None) -> None:
        from dagster._core.storage.migration.utils import upgrading_instance

        with upgrading_instance(self):
            if print_fn:
                print_fn("Updating run storage...")
            self._run_storage.upgrade()  # type: ignore  # (unknown method on run storage)
            self._run_storage.migrate(print_fn)

            if print_fn:
                print_fn("Updating event storage...")
            self._event_storage.upgrade()
            self._event_storage.reindex_assets(print_fn=print_fn)

            if print_fn:
                print_fn("Updating schedule storage...")
            self._schedule_storage.upgrade()  # type: ignore  # (possible none)
            self._schedule_storage.migrate(print_fn)  # type: ignore  # (possible none)

    def optimize_for_webserver(
        self, statement_timeout: int, pool_recycle: int, max_overflow: int
    ) -> None:
        if self._schedule_storage:
            self._schedule_storage.optimize_for_webserver(
                statement_timeout=statement_timeout,
                pool_recycle=pool_recycle,
                max_overflow=max_overflow,
            )
        self._run_storage.optimize_for_webserver(
            statement_timeout=statement_timeout,
            pool_recycle=pool_recycle,
            max_overflow=max_overflow,
        )
        self._event_storage.optimize_for_webserver(
            statement_timeout=statement_timeout,
            pool_recycle=pool_recycle,
            max_overflow=max_overflow,
        )

    def reindex(self, print_fn: PrintFn = lambda _: None) -> None:
        print_fn("Checking for reindexing...")
        self._event_storage.reindex_events(print_fn)
        self._event_storage.reindex_assets(print_fn)
        self._run_storage.optimize(print_fn)
        self._schedule_storage.optimize(print_fn)  # type: ignore  # (possible none)
        print_fn("Done.")

    def dispose(self) -> None:
        self._local_artifact_storage.dispose()
        self._run_storage.dispose()
        if self._run_coordinator:
            self._run_coordinator.dispose()
        if self._run_launcher:
            self._run_launcher.dispose()
        self._event_storage.dispose()
        if self._compute_log_manager:
            self._compute_log_manager.dispose()
        if self._secrets_loader:
            self._secrets_loader.dispose()

        if self in DagsterInstance._TEMP_DIRS:
            DagsterInstance._TEMP_DIRS[self].cleanup()
            del DagsterInstance._TEMP_DIRS[self]

    # run storage
    @public
    def get_run_by_id(self, run_id: str) -> Optional[DagsterRun]:
        """Get a :py:class:`DagsterRun` matching the provided `run_id`.

        Args:
            run_id (str): The id of the run to retrieve.

        Returns:
            Optional[DagsterRun]: The run corresponding to the given id. If no run matching the id
                is found, return `None`.
        """
        record = self.get_run_record_by_id(run_id)
        if record is None:
            return None
        return record.dagster_run

    @public
    @traced
    def get_run_record_by_id(self, run_id: str) -> Optional[RunRecord]:
        """Get a :py:class:`RunRecord` matching the provided `run_id`.

        Args:
            run_id (str): The id of the run record to retrieve.

        Returns:
            Optional[RunRecord]: The run record corresponding to the given id. If no run matching
                the id is found, return `None`.
        """
        if not run_id:
            return None
        records = self._run_storage.get_run_records(RunsFilter(run_ids=[run_id]), limit=1)
        if not records:
            return None
        return records[0]

    @traced
    def get_job_snapshot(self, snapshot_id: str) -> "JobSnap":
        return self._run_storage.get_job_snapshot(snapshot_id)

    @traced
    def has_job_snapshot(self, snapshot_id: str) -> bool:
        return self._run_storage.has_job_snapshot(snapshot_id)

    @traced
    def has_snapshot(self, snapshot_id: str) -> bool:
        return self._run_storage.has_snapshot(snapshot_id)

    @traced
    def get_historical_job(self, snapshot_id: str) -> "HistoricalJob":
        from dagster._core.remote_representation import HistoricalJob

        snapshot = self._run_storage.get_job_snapshot(snapshot_id)
        parent_snapshot = (
            self._run_storage.get_job_snapshot(snapshot.lineage_snapshot.parent_snapshot_id)
            if snapshot.lineage_snapshot
            else None
        )
        return HistoricalJob(snapshot, snapshot_id, parent_snapshot)

    @traced
    def has_historical_job(self, snapshot_id: str) -> bool:
        return self._run_storage.has_job_snapshot(snapshot_id)

    @traced
    def get_execution_plan_snapshot(self, snapshot_id: str) -> "ExecutionPlanSnapshot":
        return self._run_storage.get_execution_plan_snapshot(snapshot_id)

    @traced
    def get_run_stats(self, run_id: str) -> DagsterRunStatsSnapshot:
        return self._event_storage.get_stats_for_run(run_id)

    @traced
    def get_run_step_stats(
        self, run_id: str, step_keys: Optional[Sequence[str]] = None
    ) -> Sequence["RunStepKeyStatsSnapshot"]:
        return self._event_storage.get_step_stats_for_run(run_id, step_keys)

    @traced
    def get_run_tags(
        self,
        tag_keys: Sequence[str],
        value_prefix: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[tuple[str, set[str]]]:
        return self._run_storage.get_run_tags(
            tag_keys=tag_keys, value_prefix=value_prefix, limit=limit
        )

    @traced
    def get_run_tag_keys(self) -> Sequence[str]:
        return self._run_storage.get_run_tag_keys()

    @traced
    def get_run_group(self, run_id: str) -> Optional[tuple[str, Sequence[DagsterRun]]]:
        return self._run_storage.get_run_group(run_id)

    def create_run_for_job(
        self,
        job_def: "JobDefinition",
        execution_plan: Optional["ExecutionPlan"] = None,
        run_id: Optional[str] = None,
        run_config: Optional[Mapping[str, object]] = None,
        resolved_op_selection: Optional[AbstractSet[str]] = None,
        status: Optional[Union[DagsterRunStatus, str]] = None,
        tags: Optional[Mapping[str, str]] = None,
        root_run_id: Optional[str] = None,
        parent_run_id: Optional[str] = None,
        op_selection: Optional[Sequence[str]] = None,
        asset_selection: Optional[AbstractSet[AssetKey]] = None,
        remote_job_origin: Optional["RemoteJobOrigin"] = None,
        job_code_origin: Optional[JobPythonOrigin] = None,
        repository_load_data: Optional["RepositoryLoadData"] = None,
    ) -> DagsterRun:
        from dagster._core.definitions.job_definition import JobDefinition
        from dagster._core.execution.api import create_execution_plan
        from dagster._core.execution.plan.plan import ExecutionPlan
        from dagster._core.snap import snapshot_from_execution_plan

        check.inst_param(job_def, "pipeline_def", JobDefinition)
        check.opt_inst_param(execution_plan, "execution_plan", ExecutionPlan)

        # note that op_selection is required to execute the solid subset, which is the
        # frozenset version of the previous solid_subset.
        # op_selection is not required and will not be converted to op_selection here.
        # i.e. this function doesn't handle solid queries.
        # op_selection is only used to pass the user queries further down.
        check.opt_set_param(resolved_op_selection, "resolved_op_selection", of_type=str)
        check.opt_list_param(op_selection, "op_selection", of_type=str)
        check.opt_set_param(asset_selection, "asset_selection", of_type=AssetKey)

        # op_selection never provided
        if asset_selection or op_selection:
            # for cases when `create_run_for_pipeline` is directly called
            job_def = job_def.get_subset(
                asset_selection=asset_selection,
                op_selection=op_selection,
            )

        if not execution_plan:
            execution_plan = create_execution_plan(
                job=job_def,
                run_config=run_config,
                instance_ref=self.get_ref() if self.is_persistent else None,
                tags=tags,
                repository_load_data=repository_load_data,
            )

        return self.create_run(
            job_name=job_def.name,
            run_id=run_id,
            run_config=run_config,
            op_selection=op_selection,
            asset_selection=asset_selection,
            asset_check_selection=None,
            resolved_op_selection=resolved_op_selection,
            step_keys_to_execute=execution_plan.step_keys_to_execute,
            status=DagsterRunStatus(status) if status else None,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            job_snapshot=job_def.get_job_snapshot(),
            execution_plan_snapshot=snapshot_from_execution_plan(
                execution_plan,
                job_def.get_job_snapshot_id(),
            ),
            parent_job_snapshot=job_def.get_parent_job_snapshot(),
            remote_job_origin=remote_job_origin,
            job_code_origin=job_code_origin,
            asset_graph=job_def.asset_layer.asset_graph,
        )

    @cached_property
    def _run_domain(self):
        from dagster._core.instance.runs.run_domain import RunDomain

        return RunDomain(self)

    @cached_property
    def _asset_domain(self):
        from dagster._core.instance.assets.asset_domain import AssetDomain

        return AssetDomain(self)

    @cached_property
    def _event_domain(self):
        from dagster._core.instance.events.event_domain import EventDomain

        return EventDomain(self)

    def create_run(
        self,
        *,
        job_name: str,
        run_id: Optional[str],
        run_config: Optional[Mapping[str, object]],
        status: Optional[DagsterRunStatus],
        tags: Optional[Mapping[str, Any]],
        root_run_id: Optional[str],
        parent_run_id: Optional[str],
        step_keys_to_execute: Optional[Sequence[str]],
        execution_plan_snapshot: Optional["ExecutionPlanSnapshot"],
        job_snapshot: Optional["JobSnap"],
        parent_job_snapshot: Optional["JobSnap"],
        asset_selection: Optional[AbstractSet[AssetKey]],
        asset_check_selection: Optional[AbstractSet["AssetCheckKey"]],
        resolved_op_selection: Optional[AbstractSet[str]],
        op_selection: Optional[Sequence[str]],
        remote_job_origin: Optional["RemoteJobOrigin"],
        job_code_origin: Optional[JobPythonOrigin],
        asset_graph: "BaseAssetGraph",
    ) -> DagsterRun:
        """Create a run with the given parameters."""
        return self._run_domain.create_run(
            job_name=job_name,
            run_id=run_id,
            run_config=run_config,
            status=status,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            step_keys_to_execute=step_keys_to_execute,
            execution_plan_snapshot=execution_plan_snapshot,
            job_snapshot=job_snapshot,
            parent_job_snapshot=parent_job_snapshot,
            asset_selection=asset_selection,
            asset_check_selection=asset_check_selection,
            resolved_op_selection=resolved_op_selection,
            op_selection=op_selection,
            remote_job_origin=remote_job_origin,
            job_code_origin=job_code_origin,
            asset_graph=asset_graph,
        )

    def create_reexecuted_run(
        self,
        *,
        parent_run: DagsterRun,
        code_location: "CodeLocation",
        remote_job: "RemoteJob",
        strategy: "ReexecutionStrategy",
        extra_tags: Optional[Mapping[str, Any]] = None,
        run_config: Optional[Mapping[str, Any]] = None,
        use_parent_run_tags: bool = False,
    ) -> DagsterRun:
        return self._run_domain.create_reexecuted_run(
            parent_run=parent_run,
            code_location=code_location,
            remote_job=remote_job,
            strategy=strategy,
            extra_tags=extra_tags,
            run_config=run_config,
            use_parent_run_tags=use_parent_run_tags,
        )

    def register_managed_run(
        self,
        job_name: str,
        run_id: str,
        run_config: Optional[Mapping[str, object]],
        resolved_op_selection: Optional[AbstractSet[str]],
        step_keys_to_execute: Optional[Sequence[str]],
        tags: Mapping[str, str],
        root_run_id: Optional[str],
        parent_run_id: Optional[str],
        job_snapshot: Optional["JobSnap"],
        execution_plan_snapshot: Optional["ExecutionPlanSnapshot"],
        parent_job_snapshot: Optional["JobSnap"],
        op_selection: Optional[Sequence[str]] = None,
        job_code_origin: Optional[JobPythonOrigin] = None,
    ) -> DagsterRun:
        return self._run_domain.register_managed_run(
            job_name=job_name,
            run_id=run_id,
            run_config=run_config,
            resolved_op_selection=resolved_op_selection,
            step_keys_to_execute=step_keys_to_execute,
            tags=tags,
            root_run_id=root_run_id,
            parent_run_id=parent_run_id,
            job_snapshot=job_snapshot,
            execution_plan_snapshot=execution_plan_snapshot,
            parent_job_snapshot=parent_job_snapshot,
            op_selection=op_selection,
            job_code_origin=job_code_origin,
        )

    @traced
    def add_run(self, dagster_run: DagsterRun) -> DagsterRun:
        return self._run_storage.add_run(dagster_run)

    @traced
    def add_snapshot(
        self,
        snapshot: Union["JobSnap", "ExecutionPlanSnapshot"],
    ) -> None:
        return self._run_storage.add_snapshot(snapshot)

    @traced
    def handle_run_event(
        self, run_id: str, event: "DagsterEvent", update_timestamp: Optional[datetime] = None
    ) -> None:
        return self._run_storage.handle_run_event(run_id, event, update_timestamp)

    @traced
    def add_run_tags(self, run_id: str, new_tags: Mapping[str, str]) -> None:
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
        ascending: bool = False,
    ) -> Sequence[DagsterRun]:
        return self._run_storage.get_runs(filters, cursor, limit, bucket_by, ascending)

    @traced
    def get_run_ids(
        self,
        filters: Optional[RunsFilter] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Sequence[str]:
        return self._run_storage.get_run_ids(filters, cursor=cursor, limit=limit)

    @traced
    def get_runs_count(self, filters: Optional[RunsFilter] = None) -> int:
        return self._run_storage.get_runs_count(filters)

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

    @traced
    def get_run_partition_data(self, runs_filter: RunsFilter) -> Sequence[RunPartitionData]:
        """Get run partition data for a given partitioned job."""
        return self._run_storage.get_run_partition_data(runs_filter)

    def wipe(self) -> None:
        self._run_storage.wipe()
        self._event_storage.wipe()

    @public
    @traced
    def delete_run(self, run_id: str) -> None:
        """Delete a run and all events generated by that from storage.

        Args:
            run_id (str): The id of the run to delete.
        """
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
    ) -> Sequence["EventLogEntry"]:
        return self._event_domain.logs_after(run_id, cursor, of_type, limit)

    @traced
    def all_logs(
        self,
        run_id: str,
        of_type: Optional[Union["DagsterEventType", set["DagsterEventType"]]] = None,
    ) -> Sequence["EventLogEntry"]:
        return self._event_domain.all_logs(run_id, of_type)

    @traced
    def get_records_for_run(
        self,
        run_id: str,
        cursor: Optional[str] = None,
        of_type: Optional[Union["DagsterEventType", set["DagsterEventType"]]] = None,
        limit: Optional[int] = None,
        ascending: bool = True,
    ) -> "EventLogConnection":
        return self._event_domain.get_records_for_run(run_id, cursor, of_type, limit, ascending)

    def watch_event_logs(self, run_id: str, cursor: Optional[str], cb: "EventHandlerFn") -> None:
        return self._event_domain.watch_event_logs(run_id, cursor, cb)

    def end_watch_event_logs(self, run_id: str, cb: "EventHandlerFn") -> None:
        return self._event_domain.end_watch_event_logs(run_id, cb)

    # asset storage

    @traced
    def can_read_asset_status_cache(self) -> bool:
        return self._asset_domain.can_read_asset_status_cache()

    @traced
    def update_asset_cached_status_data(
        self, asset_key: AssetKey, cache_values: "AssetStatusCacheValue"
    ) -> None:
        self._asset_domain.update_asset_cached_status_data(asset_key, cache_values)

    @traced
    def wipe_asset_cached_status(self, asset_keys: Sequence[AssetKey]) -> None:
        self._asset_domain.wipe_asset_cached_status(asset_keys)

    @traced
    def all_asset_keys(self) -> Sequence[AssetKey]:
        return self._asset_domain.all_asset_keys()

    @public
    @traced
    def get_asset_keys(
        self,
        prefix: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Sequence[AssetKey]:
        """Return a filtered subset of asset keys managed by this instance.

        Args:
            prefix (Optional[Sequence[str]]): Return only assets having this key prefix.
            limit (Optional[int]): Maximum number of keys to return.
            cursor (Optional[str]): Cursor to use for pagination.

        Returns:
            Sequence[AssetKey]: List of asset keys.
        """
        return self._asset_domain.get_asset_keys(prefix, limit, cursor)

    @public
    @traced
    def has_asset_key(self, asset_key: AssetKey) -> bool:
        """Return true if this instance manages the given asset key.

        Args:
            asset_key (AssetKey): Asset key to check.
        """
        return self._asset_domain.has_asset_key(asset_key)

    @traced
    def get_latest_materialization_events(
        self, asset_keys: Iterable[AssetKey]
    ) -> Mapping[AssetKey, Optional["EventLogEntry"]]:
        return self._asset_domain.get_latest_materialization_events(asset_keys)

    @public
    @traced
    def get_latest_materialization_event(self, asset_key: AssetKey) -> Optional["EventLogEntry"]:
        """Fetch the latest materialization event for the given asset key.

        Args:
            asset_key (AssetKey): Asset key to return materialization for.

        Returns:
            Optional[EventLogEntry]: The latest materialization event for the given asset
                key, or `None` if the asset has not been materialized.
        """
        return self._asset_domain.get_latest_materialization_event(asset_key)

    @traced
    def get_latest_asset_check_evaluation_record(
        self, asset_check_key: "AssetCheckKey"
    ) -> Optional["AssetCheckExecutionRecord"]:
        return self._asset_domain.get_latest_asset_check_evaluation_record(asset_check_key)

    @traced
    @deprecated(breaking_version="2.0")
    def get_event_records(
        self,
        event_records_filter: "EventRecordsFilter",
        limit: Optional[int] = None,
        ascending: bool = False,
    ) -> Sequence["EventLogRecord"]:
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
        from dagster._core.events import PIPELINE_EVENTS, DagsterEventType

        if (
            event_records_filter.event_type == DagsterEventType.ASSET_MATERIALIZATION_PLANNED
            and event_records_filter.asset_partitions
        ):
            warnings.warn(
                "Asset materialization planned events with partitions subsets will not be "
                "returned when the event records filter contains the asset_partitions argument"
            )
        elif event_records_filter.event_type == DagsterEventType.ASSET_MATERIALIZATION:
            warnings.warn(
                "Use fetch_materializations instead of get_event_records to fetch materialization events."
            )
        elif event_records_filter.event_type == DagsterEventType.ASSET_OBSERVATION:
            warnings.warn(
                "Use fetch_observations instead of get_event_records to fetch observation events."
            )
        elif event_records_filter.event_type in PIPELINE_EVENTS:
            warnings.warn(
                "Use fetch_run_status_changes instead of get_event_records to fetch run status change events."
            )

        return self._event_domain.get_event_records(event_records_filter, limit, ascending)

    @public
    @traced
    def fetch_materializations(
        self,
        records_filter: Union[AssetKey, "AssetRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> "EventRecordsResult":
        """Return a list of materialization records stored in the event log storage.

        Args:
            records_filter (Union[AssetKey, AssetRecordsFilter]): the filter by which to
                filter event records.
            limit (int): Number of results to get.
            cursor (Optional[str]): Cursor to use for pagination. Defaults to None.
            ascending (Optional[bool]): Sort the result in ascending order if True, descending
                otherwise. Defaults to descending.

        Returns:
            EventRecordsResult: Object containing a list of event log records and a cursor string
        """
        return self._asset_domain.fetch_materializations(records_filter, limit, cursor, ascending)

    @traced
    def fetch_failed_materializations(
        self,
        records_filter: Union[AssetKey, "AssetRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> "EventRecordsResult":
        """Return a list of AssetFailedToMaterialization records stored in the event log storage.

        Args:
            records_filter (Union[AssetKey, AssetRecordsFilter]): the filter by which to
                filter event records.
            limit (int): Number of results to get.
            cursor (Optional[str]): Cursor to use for pagination. Defaults to None.
            ascending (Optional[bool]): Sort the result in ascending order if True, descending
                otherwise. Defaults to descending.

        Returns:
            EventRecordsResult: Object containing a list of event log records and a cursor string
        """
        return self._asset_domain.fetch_failed_materializations(
            records_filter, limit, cursor, ascending
        )

    @traced
    @deprecated(breaking_version="2.0")
    def fetch_planned_materializations(
        self,
        records_filter: Union[AssetKey, "AssetRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> "EventRecordsResult":
        """Return a list of planned materialization records stored in the event log storage.

        Args:
            records_filter (Optional[Union[AssetKey, AssetRecordsFilter]]): the filter by which to
                filter event records.
            limit (int): Number of results to get.
            cursor (Optional[str]): Cursor to use for pagination. Defaults to None.
            ascending (Optional[bool]): Sort the result in ascending order if True, descending
                otherwise. Defaults to descending.

        Returns:
            EventRecordsResult: Object containing a list of event log records and a cursor string
        """
        return self._asset_domain.fetch_planned_materializations(
            records_filter, limit, cursor, ascending
        )

    @public
    @traced
    def fetch_observations(
        self,
        records_filter: Union[AssetKey, "AssetRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> "EventRecordsResult":
        """Return a list of observation records stored in the event log storage.

        Args:
            records_filter (Optional[Union[AssetKey, AssetRecordsFilter]]): the filter by which to
                filter event records.
            limit (int): Number of results to get.
            cursor (Optional[str]): Cursor to use for pagination. Defaults to None.
            ascending (Optional[bool]): Sort the result in ascending order if True, descending
                otherwise. Defaults to descending.

        Returns:
            EventRecordsResult: Object containing a list of event log records and a cursor string
        """
        return self._event_storage.fetch_observations(records_filter, limit, cursor, ascending)

    @public
    @traced
    def fetch_run_status_changes(
        self,
        records_filter: Union["DagsterEventType", "RunStatusChangeRecordsFilter"],
        limit: int,
        cursor: Optional[str] = None,
        ascending: bool = False,
    ) -> "EventRecordsResult":
        """Return a list of run_status_event records stored in the event log storage.

        Args:
            records_filter (Optional[Union[DagsterEventType, RunStatusChangeRecordsFilter]]): the
                filter by which to filter event records.
            limit (int): Number of results to get.
            cursor (Optional[str]): Cursor to use for pagination. Defaults to None.
            ascending (Optional[bool]): Sort the result in ascending order if True, descending
                otherwise. Defaults to descending.

        Returns:
            EventRecordsResult: Object containing a list of event log records and a cursor string
        """
        return self._event_storage.fetch_run_status_changes(
            records_filter, limit, cursor, ascending
        )

    @public
    @traced
    def get_status_by_partition(
        self,
        asset_key: AssetKey,
        partition_keys: Sequence[str],
        partitions_def: "PartitionsDefinition",
    ) -> Optional[Mapping[str, "AssetPartitionStatus"]]:
        """Get the current status of provided partition_keys for the provided asset.

        Args:
            asset_key (AssetKey): The asset to get per-partition status for.
            partition_keys (Sequence[str]): The partitions to get status for.
            partitions_def (PartitionsDefinition): The PartitionsDefinition of the asset to get
                per-partition status for.

        Returns:
            Optional[Mapping[str, AssetPartitionStatus]]: status for each partition key

        """
        from dagster._core.storage.partition_status_cache import (
            AssetPartitionStatus,
            AssetStatusCacheValue,
            get_and_update_asset_status_cache_value,
        )

        cached_value = get_and_update_asset_status_cache_value(self, asset_key, partitions_def)

        if isinstance(cached_value, AssetStatusCacheValue):
            materialized_partitions = cached_value.deserialize_materialized_partition_subsets(
                partitions_def
            )
            failed_partitions = cached_value.deserialize_failed_partition_subsets(partitions_def)
            in_progress_partitions = cached_value.deserialize_in_progress_partition_subsets(
                partitions_def
            )

            status_by_partition = {}

            for partition_key in partition_keys:
                if partition_key in in_progress_partitions:
                    status_by_partition[partition_key] = AssetPartitionStatus.IN_PROGRESS
                elif partition_key in failed_partitions:
                    status_by_partition[partition_key] = AssetPartitionStatus.FAILED
                elif partition_key in materialized_partitions:
                    status_by_partition[partition_key] = AssetPartitionStatus.MATERIALIZED
                else:
                    status_by_partition[partition_key] = None

            return status_by_partition

    @public
    @traced
    def get_asset_records(
        self, asset_keys: Optional[Sequence[AssetKey]] = None
    ) -> Sequence["AssetRecord"]:
        """Return an `AssetRecord` for each of the given asset keys.

        Args:
            asset_keys (Optional[Sequence[AssetKey]]): List of asset keys to retrieve records for.

        Returns:
            Sequence[AssetRecord]: List of asset records.
        """
        return self._asset_domain.get_asset_records(asset_keys)

    @traced
    def get_event_tags_for_asset(
        self,
        asset_key: AssetKey,
        filter_tags: Optional[Mapping[str, str]] = None,
        filter_event_id: Optional[int] = None,
    ) -> Sequence[Mapping[str, str]]:
        """Fetches asset event tags for the given asset key.

        If filter_tags is provided, searches for events containing all of the filter tags. Then,
        returns all tags for those events. This enables searching for multipartitioned asset
        partition tags with a fixed dimension value, e.g. all of the tags for events where
        "country" == "US".

        If filter_event_id is provided, searches for the event with the provided event_id.

        Returns a list of dicts, where each dict is a mapping of tag key to tag value for a
        single event.
        """
        return self._asset_domain.get_event_tags_for_asset(asset_key, filter_tags, filter_event_id)

    @public
    @traced
    def wipe_assets(self, asset_keys: Sequence[AssetKey]) -> None:
        """Wipes asset event history from the event log for the given asset keys.

        Args:
            asset_keys (Sequence[AssetKey]): Asset keys to wipe.
        """
        self._asset_domain.wipe_assets(asset_keys)

    def wipe_asset_partitions(
        self,
        asset_key: AssetKey,
        partition_keys: Sequence[str],
    ) -> None:
        """Wipes asset event history from the event log for the given asset key and partition keys.

        Args:
            asset_key (AssetKey): Asset key to wipe.
            partition_keys (Sequence[str]): Partition keys to wipe.
        """
        self._asset_domain.wipe_asset_partitions(asset_key, partition_keys)

    @traced
    def get_materialized_partitions(
        self,
        asset_key: AssetKey,
        before_cursor: Optional[int] = None,
        after_cursor: Optional[int] = None,
    ) -> set[str]:
        return self._asset_domain.get_materialized_partitions(
            asset_key, before_cursor, after_cursor
        )

    @traced
    def get_latest_storage_id_by_partition(
        self,
        asset_key: AssetKey,
        event_type: "DagsterEventType",
        partitions: Optional[set[str]] = None,
    ) -> Mapping[str, int]:
        """Fetch the latest materialzation storage id for each partition for a given asset key.

        Returns a mapping of partition to storage id.
        """
        return self._asset_domain.get_latest_storage_id_by_partition(
            asset_key, event_type, partitions
        )

    @traced
    def get_latest_planned_materialization_info(
        self,
        asset_key: AssetKey,
        partition: Optional[str] = None,
    ) -> Optional["PlannedMaterializationInfo"]:
        return self._asset_domain.get_latest_planned_materialization_info(asset_key, partition)

    @public
    @traced
    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        """Get the set of partition keys for the specified :py:class:`DynamicPartitionsDefinition`.

        Args:
            partitions_def_name (str): The name of the `DynamicPartitionsDefinition`.
        """
        check.str_param(partitions_def_name, "partitions_def_name")
        return self._event_storage.get_dynamic_partitions(partitions_def_name)

    @traced
    def get_paginated_dynamic_partitions(
        self,
        partitions_def_name: str,
        limit: int,
        ascending: bool,
        cursor: Optional[str] = None,
    ) -> PaginatedResults[str]:
        """Get a paginatable subset of partition keys for the specified :py:class:`DynamicPartitionsDefinition`.

        Args:
            partitions_def_name (str): The name of the `DynamicPartitionsDefinition`.
            limit (int): Maximum number of partition keys to return.
            ascending (bool): The order of dynamic partitions to return.
            cursor (Optional[str]): Cursor to use for pagination. Defaults to None.
        """
        check.str_param(partitions_def_name, "partitions_def_name")
        check.int_param(limit, "limit")
        check.bool_param(ascending, "ascending")
        check.opt_str_param(cursor, "cursor")
        return self._event_storage.get_paginated_dynamic_partitions(
            partitions_def_name=partitions_def_name,
            limit=limit,
            ascending=ascending,
            cursor=cursor,
        )

    @public
    @traced
    def add_dynamic_partitions(
        self, partitions_def_name: str, partition_keys: Sequence[str]
    ) -> None:
        """Add partitions to the specified :py:class:`DynamicPartitionsDefinition` idempotently.
        Does not add any partitions that already exist.

        Args:
            partitions_def_name (str): The name of the `DynamicPartitionsDefinition`.
            partition_keys (Sequence[str]): Partition keys to add.
        """
        from dagster._core.definitions.partitions.utils import (
            raise_error_on_invalid_partition_key_substring,
        )

        check.str_param(partitions_def_name, "partitions_def_name")
        check.sequence_param(partition_keys, "partition_keys", of_type=str)
        if isinstance(partition_keys, str):
            # Guard against a single string being passed in `partition_keys`
            raise DagsterInvalidInvocationError("partition_keys must be a sequence of strings")
        raise_error_on_invalid_partition_key_substring(partition_keys)
        return self._event_storage.add_dynamic_partitions(partitions_def_name, partition_keys)

    @public
    @traced
    def delete_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> None:
        """Delete a partition for the specified :py:class:`DynamicPartitionsDefinition`.
        If the partition does not exist, exits silently.

        Args:
            partitions_def_name (str): The name of the `DynamicPartitionsDefinition`.
            partition_key (str): Partition key to delete.
        """
        check.str_param(partitions_def_name, "partitions_def_name")
        check.str_param(partition_key, "partition_key")
        self._event_storage.delete_dynamic_partition(partitions_def_name, partition_key)

    @public
    @traced
    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        """Check if a partition key exists for the :py:class:`DynamicPartitionsDefinition`.

        Args:
            partitions_def_name (str): The name of the `DynamicPartitionsDefinition`.
            partition_key (Sequence[str]): Partition key to check.
        """
        check.str_param(partitions_def_name, "partitions_def_name")
        check.str_param(partition_key, "partition_key")
        return self._event_storage.has_dynamic_partition(partitions_def_name, partition_key)

    # event subscriptions

    def _get_yaml_python_handlers(self) -> Sequence[logging.Handler]:
        if self._settings:
            logging_config = self.get_settings("python_logs").get("dagster_handler_config", {})

            if logging_config:
                beta_warning("Handling yaml-defined logging configuration")

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

    def _get_event_log_handler(self) -> _EventListenerLogHandler:
        event_log_handler = _EventListenerLogHandler(self)
        event_log_handler.setLevel(10)
        return event_log_handler

    def get_handlers(self) -> Sequence[logging.Handler]:
        handlers: list[logging.Handler] = [self._get_event_log_handler()]
        handlers.extend(self._get_yaml_python_handlers())
        return handlers

    def should_store_event(self, event: "EventLogEntry") -> bool:
        return self._event_domain.should_store_event(event)

    def store_event(self, event: "EventLogEntry") -> None:
        self._event_domain.store_event(event)

    def handle_new_event(
        self,
        event: "EventLogEntry",
        *,
        batch_metadata: Optional["DagsterEventBatchMetadata"] = None,
    ) -> None:
        """Handle a new event by storing it and notifying subscribers.

        Events may optionally be sent with `batch_metadata`. If batch writing is enabled, then
        events sent with `batch_metadata` will not trigger an immediate write. Instead, they will be
        kept in a batch-specific buffer (identified by `batch_metadata.id`) until either the buffer
        reaches the event batch size or the end of the batch is reached (signaled by
        `batch_metadata.is_end`). When this point is reached, all events in the buffer will be sent
        to the storage layer in a single batch. If an error occurrs during batch writing, then we
        fall back to iterative individual event writes.

        Args:
            event (EventLogEntry): The event to handle.
            batch_metadata (Optional[DagsterEventBatchMetadata]): Metadata for batch writing.
        """
        return self._event_domain.handle_new_event(event, batch_metadata=batch_metadata)

    def add_event_listener(self, run_id: str, cb) -> None:
        self._event_domain.add_event_listener(run_id, cb)

    def report_engine_event(
        self,
        message: str,
        dagster_run: Optional[DagsterRun] = None,
        engine_event_data: Optional["EngineEventData"] = None,
        cls: Optional[type[object]] = None,
        step_key: Optional[str] = None,
        job_name: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> "DagsterEvent":
        """Report a EngineEvent that occurred outside of a job execution context."""
        return self._event_domain.report_engine_event(
            message,
            dagster_run,
            engine_event_data,
            cls,
            step_key,
            job_name,
            run_id,
        )

    def report_dagster_event(
        self,
        dagster_event: "DagsterEvent",
        run_id: str,
        log_level: Union[str, int] = logging.INFO,
        batch_metadata: Optional["DagsterEventBatchMetadata"] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        """Takes a DagsterEvent and stores it in persistent storage for the corresponding DagsterRun."""
        self._event_domain.report_dagster_event(
            dagster_event, run_id, log_level, batch_metadata, timestamp
        )

    def report_run_canceling(self, run: DagsterRun, message: Optional[str] = None):
        """Report run canceling event."""
        return self._event_domain.report_run_canceling(run, message)

    def report_run_canceled(
        self,
        dagster_run: DagsterRun,
        message: Optional[str] = None,
    ) -> "DagsterEvent":
        """Report run canceled event."""
        return self._event_domain.report_run_canceled(dagster_run, message)

    def report_run_failed(
        self,
        dagster_run: DagsterRun,
        message: Optional[str] = None,
        job_failure_data: Optional["JobFailureData"] = None,
    ) -> "DagsterEvent":
        """Report run failed event."""
        return self._event_domain.report_run_failed(dagster_run, message, job_failure_data)

    # directories

    def file_manager_directory(self, run_id: str) -> str:
        return self._local_artifact_storage.file_manager_dir(run_id)

    def storage_directory(self) -> str:
        return self._local_artifact_storage.storage_dir

    def schedules_directory(self) -> str:
        return self._local_artifact_storage.schedules_dir

    # Runs coordinator

    def submit_run(self, run_id: str, workspace: "BaseWorkspaceRequestContext") -> DagsterRun:
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
        from dagster._core.run_coordinator import SubmitRunContext

        run = self.get_run_by_id(run_id)
        if run is None:
            raise DagsterInvariantViolationError(
                f"Could not load run {run_id} that was passed to submit_run"
            )

        check.not_none(
            run.remote_job_origin,
            "External pipeline origin must be set for submitted runs",
        )
        check.not_none(
            run.job_code_origin,
            "Python origin must be set for submitted runs",
        )

        try:
            submitted_run = self.run_coordinator.submit_run(
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

    def launch_run(self, run_id: str, workspace: "BaseWorkspaceRequestContext") -> DagsterRun:
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
            job_name=run.job_name,
        )
        self.report_dagster_event(launch_started_event, run_id=run.run_id)

        run = self.get_run_by_id(run_id)
        if run is None:
            check.failed(f"Failed to reload run {run_id}")

        try:
            self.run_launcher.launch_run(LaunchRunContext(dagster_run=run, workspace=workspace))
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

    def resume_run(
        self, run_id: str, workspace: "BaseWorkspaceRequestContext", attempt_number: int
    ) -> DagsterRun:
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
                    dagster_run=run,
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

    def count_resume_run_attempts(self, run_id: str) -> int:
        from dagster._daemon.monitoring import count_resume_run_attempts

        return count_resume_run_attempts(self, run_id)

    def run_will_resume(self, run_id: str) -> bool:
        if not self.run_monitoring_enabled:
            return False
        return self.count_resume_run_attempts(run_id) < self.run_monitoring_max_resume_run_attempts

    # Scheduler

    def start_schedule(self, remote_schedule: "RemoteSchedule") -> "InstigatorState":
        return self._scheduler.start_schedule(self, remote_schedule)  # type: ignore

    def stop_schedule(
        self,
        schedule_origin_id: str,
        schedule_selector_id: str,
        remote_schedule: Optional["RemoteSchedule"],
    ) -> "InstigatorState":
        return self._scheduler.stop_schedule(  # type: ignore
            self, schedule_origin_id, schedule_selector_id, remote_schedule
        )

    def reset_schedule(self, remote_schedule: "RemoteSchedule") -> "InstigatorState":
        return self._scheduler.reset_schedule(self, remote_schedule)  # type: ignore

    def scheduler_debug_info(self) -> "SchedulerDebugInfo":
        from dagster._core.definitions.run_request import InstigatorType
        from dagster._core.scheduler import SchedulerDebugInfo

        errors = []

        schedules: list[str] = []
        for schedule_state in self.all_instigator_state(instigator_type=InstigatorType.SCHEDULE):
            schedule_info: Mapping[str, Mapping[str, object]] = {
                schedule_state.instigator_name: {
                    "status": schedule_state.status.value,
                    "cron_schedule": schedule_state.instigator_data.cron_schedule,  # type: ignore
                    "schedule_origin_id": schedule_state.instigator_origin_id,
                    "repository_origin_id": schedule_state.repository_origin_id,
                }
            }

            schedules.append(yaml.safe_dump(schedule_info, default_flow_style=False))

        return SchedulerDebugInfo(
            scheduler_config_info=self._info_str_for_component("Scheduler", self.scheduler),
            scheduler_info=self.scheduler.debug_info(),  # type: ignore
            schedule_storage=schedules,
            errors=errors,
        )

    # Schedule / Sensor Storage

    def start_sensor(self, remote_sensor: "RemoteSensor") -> "InstigatorState":
        from dagster._core.definitions.run_request import InstigatorType
        from dagster._core.scheduler.instigation import (
            InstigatorState,
            InstigatorStatus,
            SensorInstigatorData,
        )

        stored_state = self.get_instigator_state(
            remote_sensor.get_remote_origin_id(), remote_sensor.selector_id
        )

        computed_state = remote_sensor.get_current_instigator_state(stored_state)
        if computed_state.is_running:
            return computed_state

        if not stored_state:
            return self.add_instigator_state(
                InstigatorState(
                    remote_sensor.get_remote_origin(),
                    InstigatorType.SENSOR,
                    InstigatorStatus.RUNNING,
                    SensorInstigatorData(
                        min_interval=remote_sensor.min_interval_seconds,
                        last_sensor_start_timestamp=get_current_timestamp(),
                        sensor_type=remote_sensor.sensor_type,
                    ),
                )
            )
        else:
            data = cast("SensorInstigatorData", stored_state.instigator_data)
            return self.update_instigator_state(
                stored_state.with_status(InstigatorStatus.RUNNING).with_data(
                    data.with_sensor_start_timestamp(get_current_timestamp())
                )
            )

    def stop_sensor(
        self,
        instigator_origin_id: str,
        selector_id: str,
        remote_sensor: Optional["RemoteSensor"],
    ) -> "InstigatorState":
        from dagster._core.definitions.run_request import InstigatorType
        from dagster._core.scheduler.instigation import (
            InstigatorState,
            InstigatorStatus,
            SensorInstigatorData,
        )

        stored_state = self.get_instigator_state(instigator_origin_id, selector_id)
        computed_state: InstigatorState
        if remote_sensor:
            computed_state = remote_sensor.get_current_instigator_state(stored_state)
        else:
            computed_state = check.not_none(stored_state)

        if not computed_state.is_running:
            return computed_state

        if not stored_state:
            assert remote_sensor
            return self.add_instigator_state(
                InstigatorState(
                    remote_sensor.get_remote_origin(),
                    InstigatorType.SENSOR,
                    InstigatorStatus.STOPPED,
                    SensorInstigatorData(
                        min_interval=remote_sensor.min_interval_seconds,
                        sensor_type=remote_sensor.sensor_type,
                    ),
                )
            )
        else:
            return self.update_instigator_state(stored_state.with_status(InstigatorStatus.STOPPED))

    def reset_sensor(self, remote_sensor: "RemoteSensor") -> "InstigatorState":
        """If the given sensor has a default sensor status, then update the status to
        `InstigatorStatus.DECLARED_IN_CODE` in instigator storage.

        Args:
            instance (DagsterInstance): The current instance.
            remote_sensor (ExternalSensor): The sensor to reset.
        """
        from dagster._core.definitions.run_request import InstigatorType
        from dagster._core.scheduler.instigation import (
            InstigatorState,
            InstigatorStatus,
            SensorInstigatorData,
        )

        stored_state = self.get_instigator_state(
            remote_sensor.get_remote_origin_id(), remote_sensor.selector_id
        )
        new_status = InstigatorStatus.DECLARED_IN_CODE

        if not stored_state:
            new_instigator_data = SensorInstigatorData(
                min_interval=remote_sensor.min_interval_seconds,
                sensor_type=remote_sensor.sensor_type,
            )

            reset_state = self.add_instigator_state(
                state=InstigatorState(
                    remote_sensor.get_remote_origin(),
                    InstigatorType.SENSOR,
                    new_status,
                    new_instigator_data,
                )
            )
        else:
            reset_state = self.update_instigator_state(state=stored_state.with_status(new_status))

        return reset_state

    @traced
    def all_instigator_state(
        self,
        repository_origin_id: Optional[str] = None,
        repository_selector_id: Optional[str] = None,
        instigator_type: Optional["InstigatorType"] = None,
        instigator_statuses: Optional[set["InstigatorStatus"]] = None,
    ):
        if not self._schedule_storage:
            check.failed("Schedule storage not available")
        return self._schedule_storage.all_instigator_state(
            repository_origin_id,
            repository_selector_id,
            instigator_type,
            instigator_statuses,
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

    def delete_instigator_state(self, origin_id: str, selector_id: str) -> None:
        return self._schedule_storage.delete_instigator_state(origin_id, selector_id)  # type: ignore  # (possible none)

    @property
    def supports_batch_tick_queries(self) -> bool:
        return self._schedule_storage and self._schedule_storage.supports_batch_queries  # type: ignore  # (possible none)

    @traced
    def get_batch_ticks(
        self,
        selector_ids: Sequence[str],
        limit: Optional[int] = None,
        statuses: Optional[Sequence["TickStatus"]] = None,
    ) -> Mapping[str, Sequence["InstigatorTick"]]:
        if not self._schedule_storage:
            return {}
        return self._schedule_storage.get_batch_ticks(selector_ids, limit, statuses)

    @traced
    def get_tick(
        self, origin_id: str, selector_id: str, timestamp: float
    ) -> Optional["InstigatorTick"]:
        matches = self._schedule_storage.get_ticks(  # type: ignore  # (possible none)
            origin_id, selector_id, before=timestamp + 1, after=timestamp - 1, limit=1
        )
        return matches[0] if len(matches) else None

    @traced
    def get_ticks(
        self,
        origin_id: str,
        selector_id: str,
        before: Optional[float] = None,
        after: Optional[float] = None,
        limit: Optional[int] = None,
        statuses: Optional[Sequence["TickStatus"]] = None,
    ) -> Sequence["InstigatorTick"]:
        return self._schedule_storage.get_ticks(  # type: ignore  # (possible none)
            origin_id,
            selector_id,
            before=before,
            after=after,
            limit=limit,
            statuses=statuses,
        )

    def create_tick(self, tick_data: "TickData") -> "InstigatorTick":
        return check.not_none(self._schedule_storage).create_tick(tick_data)

    def update_tick(self, tick: "InstigatorTick"):
        return check.not_none(self._schedule_storage).update_tick(tick)

    def purge_ticks(
        self,
        origin_id: str,
        selector_id: str,
        before: float,
        tick_statuses: Optional[Sequence["TickStatus"]] = None,
    ) -> None:
        self._schedule_storage.purge_ticks(origin_id, selector_id, before, tick_statuses)  # type: ignore  # (possible none)

    def wipe_all_schedules(self) -> None:
        if self._scheduler:
            self._scheduler.wipe(self)  # type: ignore  # (possible none)

        self._schedule_storage.wipe()  # type: ignore  # (possible none)

    def logs_path_for_schedule(self, schedule_origin_id: str) -> str:
        return self._scheduler.get_logs_path(self, schedule_origin_id)  # type: ignore  # (possible none)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exception_type: Optional[type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.dispose()

    # dagster daemon
    def add_daemon_heartbeat(self, daemon_heartbeat: "DaemonHeartbeat") -> None:
        """Called on a regular interval by the daemon."""
        self._run_storage.add_daemon_heartbeat(daemon_heartbeat)

    def get_daemon_heartbeats(self) -> Mapping[str, "DaemonHeartbeat"]:
        """Latest heartbeats of all daemon types."""
        return self._run_storage.get_daemon_heartbeats()

    def wipe_daemon_heartbeats(self) -> None:
        self._run_storage.wipe_daemon_heartbeats()

    def get_required_daemon_types(self) -> Sequence[str]:
        from dagster._core.run_coordinator import QueuedRunCoordinator
        from dagster._core.scheduler import DagsterDaemonScheduler
        from dagster._daemon.asset_daemon import AssetDaemon
        from dagster._daemon.auto_run_reexecution.event_log_consumer import EventLogConsumerDaemon
        from dagster._daemon.daemon import (
            BackfillDaemon,
            MonitoringDaemon,
            SchedulerDaemon,
            SensorDaemon,
        )
        from dagster._daemon.freshness import FreshnessDaemon
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
        if self.auto_materialize_enabled or self.auto_materialize_use_sensors:
            daemons.append(AssetDaemon.daemon_type())
        if self.freshness_enabled:
            daemons.append(FreshnessDaemon.daemon_type())
        return daemons

    def get_daemon_statuses(
        self, daemon_types: Optional[Sequence[str]] = None
    ) -> Mapping[str, "DaemonStatus"]:
        """Get the current status of the daemons. If daemon_types aren't provided, defaults to all
        required types. Returns a dict of daemon type to status.
        """
        from dagster._daemon.controller import get_daemon_statuses

        check.opt_sequence_param(daemon_types, "daemon_types", of_type=str)
        return get_daemon_statuses(
            self,
            daemon_types=daemon_types or self.get_required_daemon_types(),
            ignore_errors=True,
        )

    @property
    def daemon_skip_heartbeats_without_errors(self) -> bool:
        # If enabled, daemon threads won't write heartbeats unless they encounter an error. This is
        # enabled in cloud, where we don't need to use heartbeats to check if daemons are running, but
        # do need to surface errors to users. This is an optimization to reduce DB writes.
        return False

    # backfill
    def get_backfills(
        self,
        filters: Optional["BulkActionsFilter"] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        status: Optional["BulkActionStatus"] = None,
    ) -> Sequence["PartitionBackfill"]:
        return self._run_storage.get_backfills(
            status=status, cursor=cursor, limit=limit, filters=filters
        )

    def get_backfills_count(self, filters: Optional["BulkActionsFilter"] = None) -> int:
        return self._run_storage.get_backfills_count(filters=filters)

    def get_backfill(self, backfill_id: str) -> Optional["PartitionBackfill"]:
        return self._run_storage.get_backfill(backfill_id)

    def add_backfill(self, partition_backfill: "PartitionBackfill") -> None:
        self._run_storage.add_backfill(partition_backfill)

    def update_backfill(self, partition_backfill: "PartitionBackfill") -> None:
        self._run_storage.update_backfill(partition_backfill)

    @property
    def should_start_background_run_thread(self) -> bool:
        """Gate on a feature to start a thread that monitors for if the run should be canceled."""
        return False

    def get_tick_retention_settings(
        self, instigator_type: "InstigatorType"
    ) -> Mapping["TickStatus", int]:
        from dagster._core.definitions.run_request import InstigatorType

        retention_settings = self.get_settings("retention")

        if instigator_type == InstigatorType.SCHEDULE:
            tick_settings = retention_settings.get("schedule")
        elif instigator_type == InstigatorType.SENSOR:
            tick_settings = retention_settings.get("sensor")
        elif instigator_type == InstigatorType.AUTO_MATERIALIZE:
            tick_settings = retention_settings.get("auto_materialize")
        else:
            raise Exception(f"Unexpected instigator type {instigator_type}")

        default_tick_settings = get_default_tick_retention_settings(instigator_type)
        return get_tick_retention_settings(tick_settings, default_tick_settings)

    def get_tick_termination_check_interval(self) -> Optional[int]:
        return None

    def inject_env_vars(self, location_name: Optional[str]) -> None:
        if not self._secrets_loader:
            return

        new_env = self._secrets_loader.get_secrets_for_environment(location_name)
        for k, v in new_env.items():
            os.environ[k] = v

    def get_latest_data_version_record(
        self,
        key: AssetKey,
        is_source: Optional[bool] = None,
        partition_key: Optional[str] = None,
        before_cursor: Optional[int] = None,
        after_cursor: Optional[int] = None,
    ) -> Optional["EventLogRecord"]:
        from dagster._core.storage.event_log.base import AssetRecordsFilter

        records_filter = AssetRecordsFilter(
            asset_key=key,
            asset_partitions=[partition_key] if partition_key else None,
            before_storage_id=before_cursor,
            after_storage_id=after_cursor,
        )

        if is_source is True:
            # this is a source asset, fetch latest observation record
            return next(iter(self.fetch_observations(records_filter, limit=1).records), None)

        elif is_source is False:
            # this is not a source asset, fetch latest materialization record
            return next(iter(self.fetch_materializations(records_filter, limit=1).records), None)

        else:
            assert is_source is None
            # if is_source is None, the requested key could correspond to either a source asset or
            # materializable asset. If there is a non-null materialization, we are dealing with a
            # materializable asset and should just return that.  If not, we should check for any
            # observation records that may match.

            materialization = next(
                iter(self.fetch_materializations(records_filter, limit=1).records), None
            )
            if materialization:
                return materialization
            return next(iter(self.fetch_observations(records_filter, limit=1).records), None)

    @public
    def get_latest_materialization_code_versions(
        self, asset_keys: Iterable[AssetKey]
    ) -> Mapping[AssetKey, Optional[str]]:
        """Returns the code version used for the latest materialization of each of the provided
        assets.

        Args:
            asset_keys (Iterable[AssetKey]): The asset keys to find latest materialization code
                versions for.

        Returns:
            Mapping[AssetKey, Optional[str]]: A dictionary with a key for each of the provided asset
                keys. The values will be None if the asset has no materializations. If an asset does
                not have a code version explicitly assigned to its definitions, but was
                materialized, Dagster assigns the run ID as its code version.
        """
        return self._asset_domain.get_latest_materialization_code_versions(asset_keys)

    @public
    def report_runless_asset_event(
        self,
        asset_event: Union[
            "AssetMaterialization",
            "AssetObservation",
            "AssetCheckEvaluation",
            "FreshnessStateEvaluation",
        ],
    ):
        """Record an event log entry related to assets that does not belong to a Dagster run."""
        return self._asset_domain.report_runless_asset_event(asset_event)

    def _report_runless_asset_event(
        self,
        asset_event: Union[
            "AssetMaterialization",
            "AssetObservation",
            "AssetCheckEvaluation",
            "FreshnessStateEvaluation",
            "FreshnessStateChange",
        ],
    ):
        """Use this directly over report_runless_asset_event to emit internal events."""
        return self._asset_domain._report_runless_asset_event(asset_event)  # noqa: SLF001

    def get_freshness_state_records(
        self, keys: Sequence[AssetKey]
    ) -> Mapping[AssetKey, FreshnessStateRecord]:
        return self._event_storage.get_freshness_state_records(keys)

    def get_asset_check_support(self) -> "AssetCheckInstanceSupport":
        from dagster._core.storage.asset_check_execution_record import AssetCheckInstanceSupport

        return (
            AssetCheckInstanceSupport.SUPPORTED
            if self.event_log_storage.supports_asset_checks
            else AssetCheckInstanceSupport.NEEDS_MIGRATION
        )

    def backfill_log_storage_enabled(self) -> bool:
        return False

    def da_request_backfills(self) -> bool:
        return False

    def dagster_observe_supported(self) -> bool:
        return False

    def dagster_asset_health_queries_supported(self) -> bool:
        return False

    def can_read_failure_events_for_asset(self, asset_record: "AssetRecord") -> bool:
        return False

    def can_read_asset_failure_events(self) -> bool:
        return False

    def internal_asset_freshness_enabled(self) -> bool:
        return os.getenv("DAGSTER_ASSET_FRESHNESS_ENABLED", "").lower() == "true"

    def streamline_read_asset_health_supported(self) -> bool:
        return False

    def streamline_read_asset_health_required(self) -> bool:
        return False

    def get_asset_check_health_state_for_assets(
        self, asset_keys: Sequence[AssetKey]
    ) -> Optional[Mapping[AssetKey, Optional["AssetCheckHealthState"]]]:
        return self._asset_domain.get_asset_check_health_state_for_assets(asset_keys)

    def get_asset_freshness_health_state_for_assets(
        self, asset_keys: Sequence[AssetKey]
    ) -> Optional[Mapping[AssetKey, Optional["AssetFreshnessHealthState"]]]:
        return self._asset_domain.get_asset_freshness_health_state_for_assets(asset_keys)

    def get_asset_materialization_health_state_for_assets(
        self, asset_keys: Sequence[AssetKey]
    ) -> Optional[Mapping[AssetKey, Optional["AssetMaterializationHealthState"]]]:
        return self._asset_domain.get_asset_materialization_health_state_for_assets(asset_keys)

    def get_minimal_asset_materialization_health_state_for_assets(
        self, asset_keys: Sequence[AssetKey]
    ) -> Optional[Mapping[AssetKey, Optional["MinimalAssetMaterializationHealthState"]]]:
        return self._asset_domain.get_minimal_asset_materialization_health_state_for_assets(
            asset_keys
        )
