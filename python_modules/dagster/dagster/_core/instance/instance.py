import logging
import os
import weakref
from collections import defaultdict
from collections.abc import Mapping, Sequence
from types import TracebackType
from typing import TYPE_CHECKING, Any, Callable, Optional, Union, cast

if TYPE_CHECKING:
    from tempfile import TemporaryDirectory

import yaml
from typing_extensions import Self, TypeAlias

import dagster._check as check
from dagster._annotations import deprecated, public
from dagster._core.definitions.events import AssetKey
from dagster._core.instance.config import DAGSTER_CONFIG_YAML_FILENAME
from dagster._core.instance.mixins.asset_mixin import AssetMixin
from dagster._core.instance.mixins.domains_mixin import DomainsMixin
from dagster._core.instance.mixins.runs_mixin import RunsMixin
from dagster._core.instance.mixins.settings_mixin import SettingsMixin
from dagster._core.instance.ref import InstanceRef
from dagster._core.instance.types import DynamicPartitionsStore, InstanceType
from dagster._core.storage.dagster_run import DagsterRun
from dagster._core.types.pagination import PaginatedResults
from dagster._serdes import ConfigurableClass
from dagster._utils import PrintFn, traced

if TYPE_CHECKING:
    from dagster._core.debug import DebugRunPayload
    from dagster._core.definitions.run_request import InstigatorType
    from dagster._core.event_api import EventHandlerFn, RunStatusChangeRecordsFilter
    from dagster._core.events import (
        DagsterEvent,
        DagsterEventBatchMetadata,
        DagsterEventType,
        EngineEventData,
    )
    from dagster._core.events.log import EventLogEntry
    from dagster._core.execution.backfill import (
        BulkActionsFilter,
        BulkActionStatus,
        PartitionBackfill,
    )
    from dagster._core.launcher import RunLauncher
    from dagster._core.remote_representation import HistoricalJob, RemoteSensor
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
    from dagster._core.storage.compute_log_manager import ComputeLogManager
    from dagster._core.storage.daemon_cursor import DaemonCursorStorage
    from dagster._core.storage.event_log import EventLogStorage
    from dagster._core.storage.event_log.base import (
        EventLogRecord,
        EventRecordsFilter,
        EventRecordsResult,
    )
    from dagster._core.storage.root import LocalArtifactStorage
    from dagster._core.storage.runs import RunStorage
    from dagster._core.storage.schedules import ScheduleStorage
    from dagster._core.storage.sql import AlembicVersion
    from dagster._daemon.types import DaemonHeartbeat, DaemonStatus

DagsterInstanceOverrides: TypeAlias = Mapping[str, Any]


@public
class DagsterInstance(SettingsMixin, RunsMixin, AssetMixin, DynamicPartitionsStore, DomainsMixin):
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

        self._initialize_run_monitoring()

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
        from dagster._core.instance.factory import create_ephemeral_instance

        return create_ephemeral_instance(tempdir=tempdir, preload=preload, settings=settings)

    @public
    @staticmethod
    def get() -> "DagsterInstance":
        """Get the current `DagsterInstance` as specified by the ``DAGSTER_HOME`` environment variable.

        Returns:
            DagsterInstance: The current DagsterInstance.
        """
        from dagster._core.instance.factory import create_instance_from_dagster_home

        return create_instance_from_dagster_home()

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
        from dagster._core.instance.factory import create_local_temp_instance

        return create_local_temp_instance(tempdir=tempdir, overrides=overrides)

    @staticmethod
    def from_config(
        config_dir: str,
        config_filename: str = DAGSTER_CONFIG_YAML_FILENAME,
    ) -> "DagsterInstance":
        from dagster._core.instance.factory import create_instance_from_config

        return create_instance_from_config(config_dir, config_filename)

    @staticmethod
    def from_ref(instance_ref: InstanceRef) -> "DagsterInstance":
        from dagster._core.instance.factory import create_instance_from_ref

        return create_instance_from_ref(instance_ref)

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
            alembic_version: Optional["AlembicVersion"],
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
        self.storage_domain.optimize_for_webserver(statement_timeout, pool_recycle, max_overflow)

    def reindex(self, print_fn: PrintFn = lambda _: None) -> None:
        self.storage_domain.reindex(print_fn)

    def dispose(self) -> None:
        self.storage_domain.dispose()
        if self._run_coordinator:
            self._run_coordinator.dispose()
        if self._run_launcher:
            self._run_launcher.dispose()
        if self._compute_log_manager:
            self._compute_log_manager.dispose()
        if self._secrets_loader:
            self._secrets_loader.dispose()

        if self in DagsterInstance._TEMP_DIRS:
            DagsterInstance._TEMP_DIRS[self].cleanup()
            del DagsterInstance._TEMP_DIRS[self]

    # run storage

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
    def add_snapshot(
        self,
        snapshot: Union["JobSnap", "ExecutionPlanSnapshot"],
    ) -> None:
        return self._run_storage.add_snapshot(snapshot)

    def wipe(self) -> None:
        self._run_storage.wipe()
        self._event_storage.wipe()

    # event storage
    @traced
    def logs_after(
        self,
        run_id: str,
        cursor: Optional[int] = None,
        of_type: Optional["DagsterEventType"] = None,
        limit: Optional[int] = None,
    ) -> Sequence["EventLogEntry"]:
        return self.event_domain.logs_after(run_id, cursor, of_type, limit)

    @traced
    def all_logs(
        self,
        run_id: str,
        of_type: Optional[Union["DagsterEventType", set["DagsterEventType"]]] = None,
    ) -> Sequence["EventLogEntry"]:
        return self.event_domain.all_logs(run_id, of_type)

    def watch_event_logs(self, run_id: str, cursor: Optional[str], cb: "EventHandlerFn") -> None:
        return self.event_domain.watch_event_logs(run_id, cursor, cb)

    def end_watch_event_logs(self, run_id: str, cb: "EventHandlerFn") -> None:
        return self.event_domain.end_watch_event_logs(run_id, cb)

    # asset storage methods are now in AssetMixin

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
        return self.event_domain.get_event_records(event_records_filter, limit, ascending)

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
        return self.storage_domain.get_latest_storage_id_by_partition(
            asset_key, event_type, partitions
        )

    @public
    @traced
    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        """Get the set of partition keys for the specified :py:class:`DynamicPartitionsDefinition`.

        Args:
            partitions_def_name (str): The name of the `DynamicPartitionsDefinition`.
        """
        return self.storage_domain.get_dynamic_partitions(partitions_def_name)

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
        return self.storage_domain.get_paginated_dynamic_partitions(
            partitions_def_name, limit, ascending, cursor
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
        return self.storage_domain.add_dynamic_partitions(partitions_def_name, partition_keys)

    @public
    @traced
    def delete_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> None:
        """Delete a partition for the specified :py:class:`DynamicPartitionsDefinition`.
        If the partition does not exist, exits silently.

        Args:
            partitions_def_name (str): The name of the `DynamicPartitionsDefinition`.
            partition_key (str): Partition key to delete.
        """
        self.storage_domain.delete_dynamic_partition(partitions_def_name, partition_key)

    @public
    @traced
    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        """Check if a partition key exists for the :py:class:`DynamicPartitionsDefinition`.

        Args:
            partitions_def_name (str): The name of the `DynamicPartitionsDefinition`.
            partition_key (Sequence[str]): Partition key to check.
        """
        return self.storage_domain.has_dynamic_partition(partitions_def_name, partition_key)

    # event subscriptions

    def get_handlers(self) -> Sequence[logging.Handler]:
        """Get all logging handlers - delegates to event domain."""
        return self.event_domain.get_handlers()

    def should_store_event(self, event: "EventLogEntry") -> bool:
        return self.event_domain.should_store_event(event)

    def store_event(self, event: "EventLogEntry") -> None:
        self.event_domain.store_event(event)

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
        return self.event_domain.handle_new_event(event, batch_metadata=batch_metadata)

    def add_event_listener(self, run_id: str, cb) -> None:
        self.event_domain.add_event_listener(run_id, cb)

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
        return self.event_domain.report_engine_event(
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
        self.event_domain.report_dagster_event(
            dagster_event, run_id, log_level, batch_metadata, timestamp
        )

    # directories

    def file_manager_directory(self, run_id: str) -> str:
        return self.storage_domain.file_manager_directory(run_id)

    def storage_directory(self) -> str:
        return self.storage_domain.storage_directory()

    def schedules_directory(self) -> str:
        return self.storage_domain.schedules_directory()

    # Runs coordinator

    # Run launcher

    # Scheduler

    def start_schedule(self, remote_schedule: "RemoteSchedule") -> "InstigatorState":
        return self.scheduling_domain.start_schedule(remote_schedule)

    def stop_schedule(
        self,
        schedule_origin_id: str,
        schedule_selector_id: str,
        remote_schedule: Optional["RemoteSchedule"],
    ) -> "InstigatorState":
        return self.scheduling_domain.stop_schedule(
            schedule_origin_id, schedule_selector_id, remote_schedule
        )

    def reset_schedule(self, remote_schedule: "RemoteSchedule") -> "InstigatorState":
        return self.scheduling_domain.reset_schedule(remote_schedule)

    def scheduler_debug_info(self) -> "SchedulerDebugInfo":
        return self.scheduling_domain.scheduler_debug_info()

    # Schedule / Sensor Storage

    def start_sensor(self, remote_sensor: "RemoteSensor") -> "InstigatorState":
        return self.scheduling_domain.start_sensor(remote_sensor)

    def stop_sensor(
        self,
        instigator_origin_id: str,
        selector_id: str,
        remote_sensor: Optional["RemoteSensor"],
    ) -> "InstigatorState":
        return self.scheduling_domain.stop_sensor(instigator_origin_id, selector_id, remote_sensor)

    def reset_sensor(self, remote_sensor: "RemoteSensor") -> "InstigatorState":
        """If the given sensor has a default sensor status, then update the status to
        `InstigatorStatus.DECLARED_IN_CODE` in instigator storage.

        Args:
            instance (DagsterInstance): The current instance.
            remote_sensor (ExternalSensor): The sensor to reset.
        """
        return self.scheduling_domain.reset_sensor(remote_sensor)

    @traced
    def all_instigator_state(
        self,
        repository_origin_id: Optional[str] = None,
        repository_selector_id: Optional[str] = None,
        instigator_type: Optional["InstigatorType"] = None,
        instigator_statuses: Optional[set["InstigatorStatus"]] = None,
    ):
        return self.scheduling_domain.all_instigator_state(
            repository_origin_id, repository_selector_id, instigator_type, instigator_statuses
        )

    @traced
    def get_instigator_state(self, origin_id: str, selector_id: str) -> Optional["InstigatorState"]:
        return self.scheduling_domain.get_instigator_state(origin_id, selector_id)

    def add_instigator_state(self, state: "InstigatorState") -> "InstigatorState":
        return self.scheduling_domain.add_instigator_state(state)

    def update_instigator_state(self, state: "InstigatorState") -> "InstigatorState":
        return self.scheduling_domain.update_instigator_state(state)

    def delete_instigator_state(self, origin_id: str, selector_id: str) -> None:
        return self.scheduling_domain.delete_instigator_state(origin_id, selector_id)

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
        _exception_type: Optional[type[BaseException]],
        _exception_value: Optional[BaseException],
        _traceback: Optional[TracebackType],
    ) -> None:
        self.dispose()

    # dagster daemon
    def add_daemon_heartbeat(self, daemon_heartbeat: "DaemonHeartbeat") -> None:
        """Called on a regular interval by the daemon."""
        return self.daemon_domain.add_daemon_heartbeat(daemon_heartbeat)

    def get_daemon_heartbeats(self) -> Mapping[str, "DaemonHeartbeat"]:
        """Latest heartbeats of all daemon types."""
        return self.daemon_domain.get_daemon_heartbeats()

    def wipe_daemon_heartbeats(self) -> None:
        return self.daemon_domain.wipe_daemon_heartbeats()

    def get_required_daemon_types(self) -> Sequence[str]:
        return self.daemon_domain.get_required_daemon_types()

    def get_daemon_statuses(
        self, daemon_types: Optional[Sequence[str]] = None
    ) -> Mapping[str, "DaemonStatus"]:
        """Get the current status of the daemons. If daemon_types aren't provided, defaults to all
        required types. Returns a dict of daemon type to status.
        """
        return self.daemon_domain.get_daemon_statuses(daemon_types)

    @property
    def daemon_skip_heartbeats_without_errors(self) -> bool:
        return self.daemon_domain.daemon_skip_heartbeats_without_errors

    # backfill
    def get_backfills(
        self,
        filters: Optional["BulkActionsFilter"] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        status: Optional["BulkActionStatus"] = None,
    ) -> Sequence["PartitionBackfill"]:
        return self.scheduling_domain.get_backfills(filters, cursor, limit, status)

    def get_backfills_count(self, filters: Optional["BulkActionsFilter"] = None) -> int:
        return self.scheduling_domain.get_backfills_count(filters)

    def get_backfill(self, backfill_id: str) -> Optional["PartitionBackfill"]:
        return self.scheduling_domain.get_backfill(backfill_id)

    def add_backfill(self, partition_backfill: "PartitionBackfill") -> None:
        self.scheduling_domain.add_backfill(partition_backfill)

    def update_backfill(self, partition_backfill: "PartitionBackfill") -> None:
        self.scheduling_domain.update_backfill(partition_backfill)

    @property
    def should_start_background_run_thread(self) -> bool:
        """Gate on a feature to start a thread that monitors for if the run should be canceled."""
        return False

    def get_tick_retention_settings(
        self, instigator_type: "InstigatorType"
    ) -> Mapping["TickStatus", int]:
        return self.scheduling_domain.get_tick_retention_settings(instigator_type)

    def get_tick_termination_check_interval(self) -> Optional[int]:
        return None

    def inject_env_vars(self, location_name: Optional[str]) -> None:
        if not self._secrets_loader:
            return

        new_env = self._secrets_loader.get_secrets_for_environment(location_name)
        for k, v in new_env.items():
            os.environ[k] = v

    def backfill_log_storage_enabled(self) -> bool:
        return False

    def da_request_backfills(self) -> bool:
        return False

    def dagster_observe_supported(self) -> bool:
        return False
