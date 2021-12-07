import inspect
import logging
import logging.config
import os
import sys
import tempfile
import time
import warnings
import weakref
from collections import defaultdict
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    cast,
)

import yaml
from dagster import check
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.pipeline_base import InMemoryPipeline
from dagster.core.definitions.pipeline_definition import (
    PipelineDefinition,
    PipelineSubsetDefinition,
)
from dagster.core.errors import (
    DagsterHomeNotSetError,
    DagsterInvariantViolationError,
    DagsterRunAlreadyExists,
    DagsterRunConflict,
)
from dagster.core.storage.pipeline_run import (
    IN_PROGRESS_RUN_STATUSES,
    DagsterRun,
    PipelineRun,
    PipelineRunStatsSnapshot,
    PipelineRunStatus,
    PipelineRunsFilter,
    RunRecord,
)
from dagster.core.storage.tags import MEMOIZED_RUN_TAG
from dagster.core.system_config.objects import ResolvedRunConfig
from dagster.core.utils import str_format_list
from dagster.serdes import ConfigurableClass
from dagster.seven import get_current_datetime_in_utc
from dagster.utils.backcompat import experimental_functionality_warning
from dagster.utils.error import serializable_error_info_from_exc_info

from .config import DAGSTER_CONFIG_YAML_FILENAME, is_dagster_home_set
from .ref import InstanceRef

# 'airflow_execution_date' and 'is_airflow_ingest_pipeline' are hardcoded tags used in the
# airflow ingestion logic (see: dagster_pipeline_factory.py). 'airflow_execution_date' stores the
# 'execution_date' used in Airflow operator execution and 'is_airflow_ingest_pipeline' determines
# whether 'airflow_execution_date' is needed.
# https://github.com/dagster-io/dagster/issues/2403
AIRFLOW_EXECUTION_DATE_STR = "airflow_execution_date"
IS_AIRFLOW_INGEST_PIPELINE_STR = "is_airflow_ingest_pipeline"


if TYPE_CHECKING:
    from dagster.core.events import DagsterEvent, DagsterEventType
    from dagster.core.host_representation import HistoricalPipeline
    from dagster.core.snap import PipelineSnapshot, ExecutionPlanSnapshot
    from dagster.core.storage.event_log.base import EventRecordsFilter, EventLogRecord
    from dagster.core.workspace.workspace import IWorkspace
    from dagster.daemon.types import DaemonHeartbeat
    from dagster.core.storage.compute_log_manager import ComputeLogManager
    from dagster.core.storage.event_log import EventLogStorage
    from dagster.core.storage.root import LocalArtifactStorage
    from dagster.core.storage.runs import RunStorage
    from dagster.core.storage.schedules import ScheduleStorage
    from dagster.core.scheduler import Scheduler
    from dagster.core.run_coordinator import RunCoordinator
    from dagster.core.launcher import RunLauncher
    from dagster.core.execution.stats import RunStepKeyStatsSnapshot
    from dagster.core.debug import DebugRunPayload


def _check_run_equality(
    pipeline_run: PipelineRun, candidate_run: PipelineRun
) -> Dict[str, Tuple[Any, Any]]:
    field_diff = {}
    for field in pipeline_run._fields:
        expected_value = getattr(pipeline_run, field)
        candidate_value = getattr(candidate_run, field)
        if expected_value != candidate_value:
            field_diff[field] = (expected_value, candidate_value)

    return field_diff


def _format_field_diff(field_diff: Dict[str, Tuple[Any, Any]]) -> str:
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
        from dagster.core.events.log import construct_event_record, StructuredLoggerMessage

        try:
            event = construct_event_record(
                StructuredLoggerMessage(
                    name=record.name,
                    message=record.msg,
                    level=record.levelno,
                    meta=record.dagster_meta,
                    record=record,
                )
            )

            self._instance.handle_new_event(event)

        except Exception as e:  # pylint: disable=W0703
            logging.critical("Error during instance event listen")
            logging.exception(str(e))
            raise


class InstanceType(Enum):
    PERSISTENT = "PERSISTENT"
    EPHEMERAL = "EPHEMERAL"


class MayHaveInstanceWeakref:
    """Mixin for classes that can have a weakref back to a Dagster instance."""

    def __init__(self):
        self._instance_weakref: weakref.ReferenceType["DagsterInstance"] = None

    @property
    def _instance(self) -> "DagsterInstance":
        instance = (
            self._instance_weakref()
            # Backcompat with custom subclasses that don't call super().__init__()
            # in their own __init__ implementations
            if (hasattr(self, "_instance_weakref") and self._instance_weakref is not None)
            else None
        )
        return cast("DagsterInstance", instance)

    def register_instance(self, instance: "DagsterInstance"):
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
    For example, to use Postgres for run and event log storage, you can write a ``dagster.yaml``
    such as the following:

    .. literalinclude:: ../../../../../examples/docs_snippets/docs_snippets/deploying/postgres_dagster.yaml
       :caption: dagster.yaml
       :language: YAML

    Args:
        instance_type (InstanceType): Indicates whether the instance is ephemeral or persistent.
            Users should not attempt to set this value directly or in their ``dagster.yaml`` files.
        local_artifact_storage (LocalArtifactStorage): The local artifact storage is used to
            configure storage for any artifacts that require a local disk, such as schedules, or
            when using the filesystem system storage to manage files and intermediates. By default,
            this will be a :py:class:`dagster.core.storage.root.LocalArtifactStorage`. Configurable
            in ``dagster.yaml`` using the :py:class:`~dagster.serdes.ConfigurableClass`
            machinery.
        run_storage (RunStorage): The run storage is used to store metadata about ongoing and past
            pipeline runs. By default, this will be a
            :py:class:`dagster.core.storage.runs.SqliteRunStorage`. Configurable in ``dagster.yaml``
            using the :py:class:`~dagster.serdes.ConfigurableClass` machinery.
        event_storage (EventLogStorage): Used to store the structured event logs generated by
            pipeline runs. By default, this will be a
            :py:class:`dagster.core.storage.event_log.SqliteEventLogStorage`. Configurable in
            ``dagster.yaml`` using the :py:class:`~dagster.serdes.ConfigurableClass` machinery.
        compute_log_manager (ComputeLogManager): The compute log manager handles stdout and stderr
            logging for solid compute functions. By default, this will be a
            :py:class:`dagster.core.storage.local_compute_log_manager.LocalComputeLogManager`.
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

    _PROCESS_TEMPDIR = None

    def __init__(
        self,
        instance_type: InstanceType,
        local_artifact_storage: "LocalArtifactStorage",
        run_storage: "RunStorage",
        event_storage: "EventLogStorage",
        compute_log_manager: "ComputeLogManager",
        run_coordinator: "RunCoordinator",
        run_launcher: "RunLauncher",
        scheduler: Optional["Scheduler"] = None,
        schedule_storage: Optional["ScheduleStorage"] = None,
        settings: Optional[Dict[str, Any]] = None,
        ref: Optional[InstanceRef] = None,
    ):
        from dagster.core.storage.compute_log_manager import ComputeLogManager
        from dagster.core.storage.event_log import EventLogStorage
        from dagster.core.storage.root import LocalArtifactStorage
        from dagster.core.storage.runs import RunStorage
        from dagster.core.storage.schedules import ScheduleStorage
        from dagster.core.scheduler import Scheduler
        from dagster.core.run_coordinator import RunCoordinator
        from dagster.core.launcher import RunLauncher

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
        self._compute_log_manager.register_instance(self)
        self._scheduler = check.opt_inst_param(scheduler, "scheduler", Scheduler)

        self._schedule_storage = check.opt_inst_param(
            schedule_storage, "schedule_storage", ScheduleStorage
        )
        if self._schedule_storage:
            self._schedule_storage.register_instance(self)

        self._run_coordinator = check.inst_param(run_coordinator, "run_coordinator", RunCoordinator)
        self._run_coordinator.register_instance(self)
        if hasattr(self._run_coordinator, "initialize") and inspect.ismethod(
            getattr(self._run_coordinator, "initialize")
        ):
            warnings.warn(
                "The initialize method on RunCoordinator has been deprecated as of 0.11.0 and will "
                "no longer be called during DagsterInstance init. Instead, the DagsterInstance "
                "will be made automatically available on any run coordinator associated with a "
                "DagsterInstance. In test, you may need to call RunCoordinator.register_instance() "
                "(mixed in from MayHaveInstanceWeakref). If you need to make use of the instance "
                "to set up your custom RunCoordinator, you should override "
                "RunCoordintor.register_instance(). This warning will be removed in 0.12.0."
            )

        self._run_launcher = check.inst_param(run_launcher, "run_launcher", RunLauncher)
        self._run_launcher.register_instance(self)
        if hasattr(self._run_launcher, "initialize") and inspect.ismethod(
            getattr(self._run_launcher, "initialize")
        ):
            warnings.warn(
                "The initialize method on RunLauncher has been deprecated as of 0.11.0 and will "
                "no longer be called during DagsterInstance init. Instead, the DagsterInstance "
                "will be made automatically available on any run launcher associated with a "
                "DagsterInstance. In test, you may need to call RunLauncher.register_instance() "
                "(mixed in from MayHaveInstanceWeakref). If you need to make use of the instance "
                "to set up your custom RunLauncher, you should override "
                "RunLauncher.register_instance(). This warning will be removed in 0.12.0."
            )

        self._settings = check.opt_dict_param(settings, "settings")

        self._ref = check.opt_inst_param(ref, "ref", InstanceRef)

        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)

        if self.run_monitoring_enabled:
            check.invariant(
                self.run_launcher.supports_check_run_worker_health,
                "Run monitoring only supports select RunLaunchers",
            )

    # ctors

    @staticmethod
    def ephemeral(
        tempdir: Optional[str] = None, preload: Optional[List["DebugRunPayload"]] = None
    ) -> "DagsterInstance":
        from dagster.core.run_coordinator import DefaultRunCoordinator
        from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
        from dagster.core.storage.event_log import InMemoryEventLogStorage
        from dagster.core.storage.root import LocalArtifactStorage
        from dagster.core.storage.runs import InMemoryRunStorage
        from dagster.core.storage.noop_compute_log_manager import NoOpComputeLogManager

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
                    '\texport DAGSTER_HOME="~/dagster_home"\n'
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

        return klass(  # type: ignore
            instance_type=InstanceType.PERSISTENT,
            local_artifact_storage=instance_ref.local_artifact_storage,
            run_storage=instance_ref.run_storage,
            event_storage=instance_ref.event_storage,
            compute_log_manager=instance_ref.compute_log_manager,
            schedule_storage=instance_ref.schedule_storage,
            scheduler=instance_ref.scheduler,
            run_coordinator=instance_ref.run_coordinator,
            run_launcher=instance_ref.run_launcher,
            settings=instance_ref.settings,
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
        if DagsterInstance._PROCESS_TEMPDIR is None:
            DagsterInstance._PROCESS_TEMPDIR = tempfile.TemporaryDirectory()
        return DagsterInstance._PROCESS_TEMPDIR.name

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
            "run_launcher": self._info(self._run_launcher),
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
        elif "experimental_dagit" in telemetry_settings:
            return telemetry_settings["experimental_dagit"]
        else:
            return dagster_telemetry_enabled_default

    # run monitoring

    @property
    def run_monitoring_enabled(self) -> bool:
        if self.is_ephemeral:
            return False

        run_monitoring_enabled_default = False

        run_monitoring_settings = self.get_settings("run_monitoring")

        if not run_monitoring_settings:
            return run_monitoring_enabled_default

        if "enabled" in run_monitoring_settings:
            return run_monitoring_settings["enabled"]
        else:
            return run_monitoring_enabled_default

    @property
    def run_monitoring_settings(self) -> Dict:
        check.invariant(self.run_monitoring_enabled, "run_monitoring is not enabled")
        return self.get_settings("run_monitoring")

    @property
    def run_monitoring_start_timeout_seconds(self) -> int:
        return self.run_monitoring_settings.get("start_timeout_seconds", 180)

    @property
    def run_monitoring_max_resume_run_attempts(self) -> int:
        return self.run_monitoring_settings.get("max_resume_run_attempts", 3)

    @property
    def run_monitoring_poll_interval_seconds(self) -> int:
        return self.run_monitoring_settings.get("poll_interval_seconds", 120)

    @property
    def cancellation_thread_poll_interval_seconds(self) -> int:
        return self.get_settings("run_monitoring").get(
            "cancellation_thread_poll_interval_seconds", 10
        )

    # python logs

    @property
    def managed_python_loggers(self) -> List[str]:
        python_log_settings = self.get_settings("python_logs") or {}
        return python_log_settings.get("managed_python_loggers", [])

    @property
    def python_log_level(self) -> Optional[str]:
        python_log_settings = self.get_settings("python_logs") or {}
        return python_log_settings.get("python_log_level")

    def upgrade(self, print_fn=None):
        from dagster.core.storage.migration.utils import upgrading_instance

        with upgrading_instance(self):

            if print_fn:
                print_fn("Updating run storage...")
            self._run_storage.upgrade()
            self._run_storage.build_missing_indexes(print_fn=print_fn)

            if print_fn:
                print_fn("Updating event storage...")
            self._event_storage.upgrade()
            self._event_storage.reindex_assets(print_fn=print_fn)

            if print_fn:
                print_fn("Updating schedule storage...")
            self._schedule_storage.upgrade()

    def optimize_for_dagit(self, statement_timeout):
        if self._schedule_storage:
            self._schedule_storage.optimize_for_dagit(statement_timeout=statement_timeout)
        self._run_storage.optimize_for_dagit(statement_timeout=statement_timeout)
        self._event_storage.optimize_for_dagit(statement_timeout=statement_timeout)

    def reindex(self, print_fn=lambda _: None):
        print_fn("Checking for reindexing...")
        self._event_storage.reindex_events(print_fn)
        self._event_storage.reindex_assets(print_fn)
        print_fn("Done.")

    def dispose(self):
        self._run_storage.dispose()
        self.run_coordinator.dispose()
        self._run_launcher.dispose()
        self._event_storage.dispose()
        self._compute_log_manager.dispose()

    # run storage

    def get_run_by_id(self, run_id: str) -> Optional[PipelineRun]:
        return self._run_storage.get_run_by_id(run_id)

    def get_pipeline_snapshot(self, snapshot_id: str) -> "PipelineSnapshot":
        return self._run_storage.get_pipeline_snapshot(snapshot_id)

    def has_pipeline_snapshot(self, snapshot_id: str) -> bool:
        return self._run_storage.has_pipeline_snapshot(snapshot_id)

    def has_snapshot(self, snapshot_id: str) -> bool:
        return self._run_storage.has_snapshot(snapshot_id)

    def get_historical_pipeline(self, snapshot_id: str) -> "HistoricalPipeline":
        from dagster.core.host_representation import HistoricalPipeline

        snapshot = self._run_storage.get_pipeline_snapshot(snapshot_id)
        parent_snapshot = (
            self._run_storage.get_pipeline_snapshot(snapshot.lineage_snapshot.parent_snapshot_id)
            if snapshot.lineage_snapshot
            else None
        )
        return HistoricalPipeline(snapshot, snapshot_id, parent_snapshot)

    def has_historical_pipeline(self, snapshot_id: str) -> bool:
        return self._run_storage.has_pipeline_snapshot(snapshot_id)

    def get_execution_plan_snapshot(self, snapshot_id: str) -> "ExecutionPlanSnapshot":
        return self._run_storage.get_execution_plan_snapshot(snapshot_id)

    def get_run_stats(self, run_id: str) -> PipelineRunStatsSnapshot:
        return self._event_storage.get_stats_for_run(run_id)

    def get_run_step_stats(self, run_id, step_keys=None) -> List["RunStepKeyStatsSnapshot"]:
        return self._event_storage.get_step_stats_for_run(run_id, step_keys)

    def get_run_tags(self) -> List[Tuple[str, Set[str]]]:
        return self._run_storage.get_run_tags()

    def get_run_group(self, run_id: str) -> Optional[Tuple[str, Iterable[PipelineRun]]]:
        return self._run_storage.get_run_group(run_id)

    def create_run_for_pipeline(
        self,
        pipeline_def,
        execution_plan=None,
        run_id=None,
        run_config=None,
        mode=None,
        solids_to_execute=None,
        status=None,
        tags=None,
        root_run_id=None,
        parent_run_id=None,
        solid_selection=None,
        external_pipeline_origin=None,
        pipeline_code_origin=None,
    ):
        from dagster.core.execution.plan.plan import ExecutionPlan
        from dagster.core.execution.api import create_execution_plan
        from dagster.core.snap import snapshot_from_execution_plan

        check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
        check.opt_inst_param(execution_plan, "execution_plan", ExecutionPlan)

        # note that solids_to_execute is required to execute the solid subset, which is the
        # frozenset version of the previous solid_subset.
        # solid_selection is not required and will not be converted to solids_to_execute here.
        # i.e. this function doesn't handle solid queries.
        # solid_selection is only used to pass the user queries further down.
        check.opt_set_param(solids_to_execute, "solids_to_execute", of_type=str)
        check.opt_list_param(solid_selection, "solid_selection", of_type=str)

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
            )

        return self.create_run(
            pipeline_name=pipeline_def.name,
            run_id=run_id,
            run_config=run_config,
            mode=check.opt_str_param(mode, "mode", default=pipeline_def.get_default_mode_name()),
            solid_selection=solid_selection,
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
        solid_selection=None,
        external_pipeline_origin=None,
        pipeline_code_origin=None,
    ):

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
        )

    def _ensure_persisted_pipeline_snapshot(self, pipeline_snapshot, parent_pipeline_snapshot):
        from dagster.core.snap import create_pipeline_snapshot_id, PipelineSnapshot

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
        from dagster.core.snap.execution_plan_snapshot import (
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
        solid_selection=None,
        external_pipeline_origin=None,
        pipeline_code_origin=None,
    ):

        pipeline_run = self._construct_run_with_snapshots(
            pipeline_name=pipeline_name,
            run_id=run_id,
            run_config=run_config,
            mode=mode,
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
        return self._run_storage.add_run(pipeline_run)

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

    def add_run(self, pipeline_run: PipelineRun):
        return self._run_storage.add_run(pipeline_run)

    def add_snapshot(self, snapshot, snapshot_id=None):
        return self._run_storage.add_snapshot(snapshot, snapshot_id)

    def handle_run_event(self, run_id: str, event: "DagsterEvent"):
        return self._run_storage.handle_run_event(run_id, event)

    def add_run_tags(self, run_id: str, new_tags: Dict[str, str]):
        return self._run_storage.add_run_tags(run_id, new_tags)

    def has_run(self, run_id: str) -> bool:
        return self._run_storage.has_run(run_id)

    def get_runs(
        self, filters: PipelineRunsFilter = None, cursor: str = None, limit: int = None
    ) -> Iterable[PipelineRun]:
        return self._run_storage.get_runs(filters, cursor, limit)

    def get_runs_count(self, filters: PipelineRunsFilter = None) -> int:
        return self._run_storage.get_runs_count(filters)

    def get_run_groups(
        self, filters: PipelineRunsFilter = None, cursor: str = None, limit: int = None
    ) -> Dict[str, Dict[str, Union[Iterable[PipelineRun], int]]]:
        return self._run_storage.get_run_groups(filters=filters, cursor=cursor, limit=limit)

    def get_run_records(
        self,
        filters: PipelineRunsFilter = None,
        limit: int = None,
        order_by: str = None,
        ascending: bool = False,
    ) -> List[RunRecord]:
        """Return a list of run records stored in the run storage, sorted by the given column in given order.

        Args:
            filters (Optional[PipelineRunsFilter]): the filter by which to filter runs.
            limit (Optional[int]): Number of results to get. Defaults to infinite.
            order_by (Optional[str]): Name of the column to sort by. Defaults to id.
            ascending (Optional[bool]): Sort the result in ascending order if True, descending
                otherwise. Defaults to descending.

        Returns:
            List[RunRecord]: List of run records stored in the run storage.
        """
        return self._run_storage.get_run_records(filters, limit, order_by, ascending)

    def wipe(self):
        self._run_storage.wipe()
        self._event_storage.wipe()

    def delete_run(self, run_id: str):
        self._run_storage.delete_run(run_id)
        self._event_storage.delete_events(run_id)

    # event storage

    def logs_after(
        self,
        run_id,
        cursor,
        of_type: "DagsterEventType" = None,
        limit: Optional[int] = None,
    ):
        return self._event_storage.get_logs_for_run(
            run_id,
            cursor=cursor,
            of_type=of_type,
            limit=limit,
        )

    def all_logs(self, run_id, of_type: "DagsterEventType" = None):
        return self._event_storage.get_logs_for_run(run_id, of_type=of_type)

    def watch_event_logs(self, run_id, cursor, cb):
        return self._event_storage.watch(run_id, cursor, cb)

    def end_watch_event_logs(self, run_id, cb):
        return self._event_storage.end_watch(run_id, cb)

    # asset storage

    def all_asset_keys(self):
        return self._event_storage.all_asset_keys()

    def get_asset_keys(self, prefix=None, limit=None, cursor=None):
        return self._event_storage.get_asset_keys(prefix=prefix, limit=limit, cursor=cursor)

    def has_asset_key(self, asset_key: AssetKey) -> bool:
        return self._event_storage.has_asset_key(asset_key)

    def get_event_records(
        self,
        event_records_filter: Optional["EventRecordsFilter"] = None,
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

    def events_for_asset_key(
        self,
        asset_key,
        partitions=None,
        before_cursor=None,
        after_cursor=None,
        cursor=None,
        before_timestamp=None,
        limit=None,
        ascending=False,
    ):
        check.inst_param(asset_key, "asset_key", AssetKey)

        warnings.warn(
            """
The method `events_for_asset_key` on DagsterInstance has been deprecated as of `0.12.0` in favor of
the method `get_event_records`. The method `get_event_records` takes in an `EventRecordsFilter`
argument that allows for filtering by asset key and asset key partitions. The return value is a
list of `EventLogRecord` objects, each of which contains a storage_id and an event log entry.

Example:
records = instance.get_event_records(
    EventRecordsFilter(
        asset_key=asset_key,
        asset_partitions=partitions,
        after_cursor=after_cursor,
    ),
)
"""
        )

        return self._event_storage.get_asset_events(
            asset_key,
            partitions,
            before_cursor,
            after_cursor,
            limit,
            before_timestamp=before_timestamp,
            ascending=ascending,
            include_cursor=True,
            cursor=cursor,
        )

    def run_ids_for_asset_key(self, asset_key):
        check.inst_param(asset_key, "asset_key", AssetKey)
        return self._event_storage.get_asset_run_ids(asset_key)

    def all_asset_tags(self):
        return self._event_storage.all_asset_tags()

    def get_asset_tags(self, asset_key):
        check.inst_param(asset_key, "asset_key", AssetKey)
        return self._event_storage.get_asset_tags(asset_key)

    def wipe_assets(self, asset_keys):
        check.list_param(asset_keys, "asset_keys", of_type=AssetKey)
        for asset_key in asset_keys:
            self._event_storage.wipe_asset(asset_key)

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
        pipeline_run,
        engine_event_data=None,
        cls=None,
        step_key=None,
    ):
        """
        Report a EngineEvent that occurred outside of a pipeline execution context.
        """
        from dagster.core.events import EngineEventData, DagsterEvent, DagsterEventType
        from dagster.core.events.log import EventLogEntry

        check.class_param(cls, "cls")
        check.str_param(message, "message")
        check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
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
            pipeline_name=pipeline_run.pipeline_name,
            message=message,
            event_specific_data=engine_event_data,
            step_key=step_key,
        )
        event_record = EventLogEntry(
            message=message,
            user_message=message,
            level=log_level,
            pipeline_name=pipeline_run.pipeline_name,
            run_id=pipeline_run.run_id,
            error_info=None,
            timestamp=time.time(),
            step_key=step_key,
            dagster_event=dagster_event,
        )

        self.handle_new_event(event_record)
        return dagster_event

    def report_run_canceling(self, run, message=None):

        from dagster.core.events import DagsterEvent, DagsterEventType
        from dagster.core.events.log import EventLogEntry

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

        event_record = EventLogEntry(
            message=message,
            user_message="",
            level=logging.INFO,
            pipeline_name=run.pipeline_name,
            run_id=run.run_id,
            error_info=None,
            timestamp=time.time(),
            dagster_event=canceling_event,
        )

        self.handle_new_event(event_record)

    def report_run_canceled(
        self,
        pipeline_run,
        message=None,
    ):
        from dagster.core.events import DagsterEvent, DagsterEventType
        from dagster.core.events.log import EventLogEntry

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
        event_record = EventLogEntry(
            message=message,
            user_message=message,
            level=logging.ERROR,
            pipeline_name=pipeline_run.pipeline_name,
            run_id=pipeline_run.run_id,
            error_info=None,
            timestamp=time.time(),
            dagster_event=dagster_event,
        )

        self.handle_new_event(event_record)
        return dagster_event

    def report_run_failed(self, pipeline_run, message=None):
        from dagster.core.events import DagsterEvent, DagsterEventType
        from dagster.core.events.log import EventLogEntry

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
        event_record = EventLogEntry(
            message=message,
            user_message=message,
            level=logging.ERROR,
            pipeline_name=pipeline_run.pipeline_name,
            run_id=pipeline_run.run_id,
            error_info=None,
            timestamp=time.time(),
            dagster_event=dagster_event,
        )

        self.handle_new_event(event_record)
        return dagster_event

    # directories

    def file_manager_directory(self, run_id):
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

        from dagster.core.host_representation import ExternalPipelineOrigin
        from dagster.core.origin import PipelinePythonOrigin
        from dagster.core.run_coordinator import SubmitRunContext

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
            from dagster.core.events import EngineEventData

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
        from dagster.core.launcher import LaunchRunContext
        from dagster.core.events import EngineEventData, DagsterEvent, DagsterEventType
        from dagster.core.events.log import EventLogEntry

        run = self.get_run_by_id(run_id)
        if run is None:
            raise DagsterInvariantViolationError(
                f"Could not load run {run_id} that was passed to launch_run"
            )

        launch_started_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_STARTING.value,
            pipeline_name=run.pipeline_name,
        )

        event_record = EventLogEntry(
            message="",
            user_message="",
            level=logging.INFO,
            pipeline_name=run.pipeline_name,
            run_id=run.run_id,
            error_info=None,
            timestamp=time.time(),
            dagster_event=launch_started_event,
        )

        self.handle_new_event(event_record)

        run = self.get_run_by_id(run_id)
        if run is None:
            check.failed(f"Failed to reload run {run_id}")

        try:
            self._run_launcher.launch_run(LaunchRunContext(pipeline_run=run, workspace=workspace))
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
        from dagster.core.launcher import LaunchRunContext
        from dagster.core.events import EngineEventData
        from dagster.daemon.monitoring import RESUME_RUN_LOG_MESSAGE

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
            self._run_launcher.launch_run(
                LaunchRunContext(
                    pipeline_run=run,
                    workspace=workspace,
                    resume_from_failure=True,
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
        from dagster.daemon.monitoring import RESUME_RUN_LOG_MESSAGE
        from dagster.core.events import DagsterEventType

        events = self.all_logs(run_id, of_type=DagsterEventType.ENGINE_EVENT)
        return len([event for event in events if event.message == RESUME_RUN_LOG_MESSAGE])

    def run_will_resume(self, run_id: str):
        if not self.run_monitoring_enabled:
            return False
        return self.count_resume_run_attempts(run_id) < self.run_monitoring_max_resume_run_attempts

    # Scheduler

    def start_schedule_and_update_storage_state(self, external_schedule):
        return self._scheduler.start_schedule_and_update_storage_state(self, external_schedule)

    def stop_schedule_and_update_storage_state(self, schedule_origin_id):
        return self._scheduler.stop_schedule_and_update_storage_state(self, schedule_origin_id)

    def stop_schedule_and_delete_from_storage(self, schedule_origin_id):
        return self._scheduler.stop_schedule_and_delete_from_storage(self, schedule_origin_id)

    def running_schedule_count(self, schedule_origin_id):
        if self._scheduler:
            return self._scheduler.running_schedule_count(self, schedule_origin_id)
        return 0

    def scheduler_debug_info(self):
        from dagster.core.scheduler import SchedulerDebugInfo
        from dagster.core.definitions.run_request import JobType
        from dagster.core.scheduler.job import JobStatus

        errors = []

        schedules = []
        for schedule_state in self.all_stored_job_state(job_type=JobType.SCHEDULE):
            if schedule_state.status == JobStatus.RUNNING and not self.running_schedule_count(
                schedule_state.job_origin_id
            ):
                errors.append(
                    "Schedule {schedule_name} is set to be running, but the scheduler is not "
                    "running the schedule.".format(schedule_name=schedule_state.job_name)
                )
            elif schedule_state.status == JobStatus.STOPPED and self.running_schedule_count(
                schedule_state.job_origin_id
            ):
                errors.append(
                    "Schedule {schedule_name} is set to be stopped, but the scheduler is still running "
                    "the schedule.".format(schedule_name=schedule_state.job_name)
                )

            if self.running_schedule_count(schedule_state.job_origin_id) > 1:
                errors.append(
                    "Duplicate jobs found: More than one job for schedule {schedule_name} are "
                    "running on the scheduler.".format(schedule_name=schedule_state.job_name)
                )

            schedule_info = {
                schedule_state.job_name: {
                    "status": schedule_state.status.value,
                    "cron_schedule": schedule_state.job_specific_data.cron_schedule,
                    "repository_pointer": schedule_state.origin.get_repo_cli_args(),
                    "schedule_origin_id": schedule_state.job_origin_id,
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

    # Schedule Storage

    def start_sensor(self, external_sensor):
        from dagster.core.scheduler.job import JobState, JobStatus, SensorJobData
        from dagster.core.definitions.run_request import JobType

        job_state = self.get_job_state(external_sensor.get_external_origin_id())

        if not job_state:
            self.add_job_state(
                JobState(
                    external_sensor.get_external_origin(),
                    JobType.SENSOR,
                    JobStatus.RUNNING,
                    SensorJobData(min_interval=external_sensor.min_interval_seconds),
                )
            )
        elif job_state.status != JobStatus.RUNNING:
            self.update_job_state(job_state.with_status(JobStatus.RUNNING))

    def stop_sensor(self, job_origin_id):
        from dagster.core.scheduler.job import JobStatus

        job_state = self.get_job_state(job_origin_id)
        if job_state:
            self.update_job_state(job_state.with_status(JobStatus.STOPPED))

    def all_stored_job_state(self, repository_origin_id=None, job_type=None):
        return self._schedule_storage.all_stored_job_state(repository_origin_id, job_type)

    def get_job_state(self, job_origin_id):
        return self._schedule_storage.get_job_state(job_origin_id)

    def add_job_state(self, job_state):
        return self._schedule_storage.add_job_state(job_state)

    def update_job_state(self, job_state):
        return self._schedule_storage.update_job_state(job_state)

    def delete_job_state(self, job_origin_id):
        return self._schedule_storage.delete_job_state(job_origin_id)

    def get_job_tick(self, job_origin_id, timestamp):
        matches = self._schedule_storage.get_job_ticks(
            job_origin_id, before=timestamp + 1, after=timestamp - 1, limit=1
        )
        return matches[0] if len(matches) else None

    def get_job_ticks(self, job_origin_id, before=None, after=None, limit=None):
        return self._schedule_storage.get_job_ticks(
            job_origin_id, before=before, after=after, limit=limit
        )

    def get_latest_job_tick(self, job_origin_id):
        return self._schedule_storage.get_latest_job_tick(job_origin_id)

    def create_job_tick(self, job_tick_data):
        return self._schedule_storage.create_job_tick(job_tick_data)

    def update_job_tick(self, tick):
        return self._schedule_storage.update_job_tick(tick)

    def get_job_tick_stats(self, job_origin_id):
        return self._schedule_storage.get_job_tick_stats(job_origin_id)

    def purge_job_ticks(self, job_origin_id, tick_status, before):
        self._schedule_storage.purge_job_ticks(job_origin_id, tick_status, before)

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

    def get_addresses_for_step_output_versions(self, step_output_versions):
        """
        For each given step output, finds whether an output exists with the given
        version, and returns its address if it does.

        Args:
            step_output_versions (Dict[(str, StepOutputHandle), str]):
                (pipeline name, step output handle) -> version.

        Returns:
            Dict[(str, StepOutputHandle), str]: (pipeline name, step output handle) -> address.
                For each step output, an address if there is one and None otherwise.
        """
        return self._event_storage.get_addresses_for_step_output_versions(step_output_versions)

    # dagster daemon
    def add_daemon_heartbeat(self, daemon_heartbeat: "DaemonHeartbeat"):
        """Called on a regular interval by the daemon"""
        self._run_storage.add_daemon_heartbeat(daemon_heartbeat)

    def get_daemon_heartbeats(self) -> Dict[str, "DaemonHeartbeat"]:
        """Latest heartbeats of all daemon types"""
        return self._run_storage.get_daemon_heartbeats()

    def wipe_daemon_heartbeats(self):
        self._run_storage.wipe_daemon_heartbeats()

    def get_required_daemon_types(self):
        from dagster.core.run_coordinator import QueuedRunCoordinator
        from dagster.core.scheduler import DagsterDaemonScheduler
        from dagster.daemon.daemon import (
            SchedulerDaemon,
            SensorDaemon,
            BackfillDaemon,
            MonitoringDaemon,
        )
        from dagster.daemon.run_coordinator.queued_run_coordinator_daemon import (
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
        return daemons

    # backfill
    def get_backfills(self, status=None, cursor=None, limit=None):
        return self._run_storage.get_backfills(status=status, cursor=cursor, limit=limit)

    def get_backfill(self, backfill_id):
        return self._run_storage.get_backfill(backfill_id)

    def add_backfill(self, partition_backfill):
        self._run_storage.add_backfill(partition_backfill)

    def update_backfill(self, partition_backfill):
        return self._run_storage.update_backfill(partition_backfill)

    @property
    def should_start_background_run_thread(self) -> bool:
        """
        Gate on an experimental feature to start a thread that monitors for if the run should be canceled.
        """
        return False


def is_dagit_telemetry_enabled(instance):
    telemetry_settings = instance.get_settings("telemetry")
    if not telemetry_settings:
        return False

    if "experimental_dagit" in telemetry_settings:
        return telemetry_settings["experimental_dagit"]
    else:
        return False
