import os
import weakref
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from contextlib import ExitStack
from types import TracebackType
from typing import TYPE_CHECKING, Any, Callable, Optional, Union, cast

if TYPE_CHECKING:
    from tempfile import TemporaryDirectory

import yaml
from typing_extensions import Self, TypeAlias

import dagster._check as check
from dagster._annotations import public
from dagster._core.instance.config import DAGSTER_CONFIG_YAML_FILENAME
from dagster._core.instance.methods.asset_methods import AssetMethods
from dagster._core.instance.methods.daemon_methods import DaemonMethods
from dagster._core.instance.methods.event_methods import EventMethods
from dagster._core.instance.methods.run_launcher_methods import RunLauncherMethods
from dagster._core.instance.methods.run_methods import RunMethods
from dagster._core.instance.methods.scheduling_methods import SchedulingMethods
from dagster._core.instance.methods.settings_methods import SettingsMethods
from dagster._core.instance.methods.storage_methods import StorageMethods
from dagster._core.instance.ref import InstanceRef
from dagster._core.instance.types import DynamicPartitionsStore, InstanceType
from dagster._core.storage.dagster_run import DagsterRun, RunsFilter
from dagster._serdes import ConfigurableClass
from dagster._utils import PrintFn, traced

if TYPE_CHECKING:
    from dagster._core.debug import DebugRunPayload
    from dagster._core.definitions.asset_checks.asset_check_evaluation import AssetCheckEvaluation
    from dagster._core.definitions.events import AssetKey, AssetObservation
    from dagster._core.definitions.freshness import FreshnessStateChange, FreshnessStateEvaluation
    from dagster._core.definitions.partitions.definition import PartitionsDefinition
    from dagster._core.event_api import AssetRecordsFilter, RunStatusChangeRecordsFilter
    from dagster._core.events import AssetMaterialization, DagsterEventType
    from dagster._core.events.log import EventLogEntry
    from dagster._core.launcher import RunLauncher
    from dagster._core.remote_representation.historical import HistoricalJob
    from dagster._core.run_coordinator import RunCoordinator
    from dagster._core.scheduler import Scheduler
    from dagster._core.secrets import SecretsLoader
    from dagster._core.snap import ExecutionPlanSnapshot, JobSnap
    from dagster._core.storage.compute_log_manager import ComputeLogManager
    from dagster._core.storage.daemon_cursor import DaemonCursorStorage
    from dagster._core.storage.dagster_run import JobBucket, RunRecord, TagBucket
    from dagster._core.storage.defs_state.base import DefsStateStorage
    from dagster._core.storage.event_log import EventLogStorage
    from dagster._core.storage.event_log.base import (
        AssetRecord,
        EventLogConnection,
        EventRecordsResult,
    )
    from dagster._core.storage.partition_status_cache import AssetPartitionStatus
    from dagster._core.storage.root import LocalArtifactStorage
    from dagster._core.storage.runs import RunStorage
    from dagster._core.storage.schedules import ScheduleStorage
    from dagster._core.storage.sql import AlembicVersion

DagsterInstanceOverrides: TypeAlias = Mapping[str, Any]


@public
class DagsterInstance(
    SettingsMethods,
    StorageMethods,
    DaemonMethods,
    RunLauncherMethods,
    EventMethods,
    SchedulingMethods,
    AssetMethods,
    RunMethods,
    DynamicPartitionsStore,
):
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
        defs_state_storage: Optional["DefsStateStorage"] = None,
        ref: Optional[InstanceRef] = None,
        **_kwargs: Any,  # we accept kwargs for forward-compat of custom instances
    ):
        from dagster._core.launcher import RunLauncher
        from dagster._core.run_coordinator import RunCoordinator
        from dagster._core.scheduler import Scheduler
        from dagster._core.secrets import SecretsLoader
        from dagster._core.storage.compute_log_manager import ComputeLogManager
        from dagster._core.storage.defs_state import DefsStateStorage
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

        self._defs_state_storage = check.opt_inst_param(
            defs_state_storage, "defs_state_storage", DefsStateStorage
        )
        if self._defs_state_storage:
            self._defs_state_storage.register_instance(self)

        self._ref = check.opt_inst_param(ref, "ref", InstanceRef)

        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

        self._initialize_run_monitoring()

        # Used for batched event handling
        self._event_buffer: dict[str, list[EventLogEntry]] = defaultdict(list)

    # =====================================================================================
    # PUBLIC API METHODS
    # =====================================================================================

    # Factory Methods
    # ---------------

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

    # Asset Domain
    # ------------

    @public
    @traced
    def fetch_materializations(
        self,
        records_filter: Union["AssetKey", "AssetRecordsFilter"],
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
        return AssetMethods.fetch_materializations(self, records_filter, limit, cursor, ascending)

    @public
    @traced
    def fetch_observations(
        self,
        records_filter: Union["AssetKey", "AssetRecordsFilter"],
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
    def get_asset_keys(
        self,
        prefix: Optional[Sequence[str]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Sequence["AssetKey"]:
        """Return a filtered subset of asset keys managed by this instance.

        Args:
            prefix (Optional[Sequence[str]]): Return only assets having this key prefix.
            limit (Optional[int]): Maximum number of keys to return.
            cursor (Optional[str]): Cursor to use for pagination.

        Returns:
            Sequence[AssetKey]: List of asset keys.
        """
        return AssetMethods.get_asset_keys(self, prefix, limit, cursor)

    @public
    @traced
    def get_asset_records(
        self, asset_keys: Optional[Sequence["AssetKey"]] = None
    ) -> Sequence["AssetRecord"]:
        """Return an `AssetRecord` for each of the given asset keys.

        Args:
            asset_keys (Optional[Sequence[AssetKey]]): List of asset keys to retrieve records for.

        Returns:
            Sequence[AssetRecord]: List of asset records.
        """
        return AssetMethods.get_asset_records(self, asset_keys)

    @public
    def get_latest_materialization_code_versions(
        self, asset_keys: Iterable["AssetKey"]
    ) -> Mapping["AssetKey", Optional[str]]:
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
        return AssetMethods.get_latest_materialization_code_versions(self, asset_keys)

    @public
    @traced
    def get_latest_materialization_event(self, asset_key: "AssetKey") -> Optional["EventLogEntry"]:
        """Fetch the latest materialization event for the given asset key.

        Args:
            asset_key (AssetKey): Asset key to return materialization for.

        Returns:
            Optional[EventLogEntry]: The latest materialization event for the given asset
                key, or `None` if the asset has not been materialized.
        """
        return AssetMethods.get_latest_materialization_event(self, asset_key)

    @public
    @traced
    def get_status_by_partition(
        self,
        asset_key: "AssetKey",
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
        return AssetMethods.get_status_by_partition(self, asset_key, partition_keys, partitions_def)

    @public
    @traced
    def has_asset_key(self, asset_key: "AssetKey") -> bool:
        """Return true if this instance manages the given asset key.

        Args:
            asset_key (AssetKey): Asset key to check.
        """
        return AssetMethods.has_asset_key(self, asset_key)

    @public
    def report_runless_asset_event(
        self,
        asset_event: Union[
            "AssetMaterialization",
            "AssetObservation",
            "AssetCheckEvaluation",
            "FreshnessStateEvaluation",
            "FreshnessStateChange",
        ],
    ):
        """Record an event log entry related to assets that does not belong to a Dagster run."""
        return AssetMethods.report_runless_asset_event(self, asset_event)

    @public
    @traced
    def wipe_assets(self, asset_keys: Sequence["AssetKey"]) -> None:
        """Wipes asset event history from the event log for the given asset keys.

        Args:
            asset_keys (Sequence[AssetKey]): Asset keys to wipe.
        """
        AssetMethods.wipe_assets(self, asset_keys)

    # Run Domain
    # ----------

    @public
    @traced
    def delete_run(self, run_id: str) -> None:
        """Delete a run and all events generated by that from storage.

        Args:
            run_id (str): The id of the run to delete.
        """
        self._run_storage.delete_run(run_id)
        self._event_storage.delete_events(run_id)

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
    def get_run_record_by_id(self, run_id: str) -> Optional["RunRecord"]:
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

    @public
    @traced
    def get_run_records(
        self,
        filters: Optional["RunsFilter"] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        ascending: bool = False,
        cursor: Optional[str] = None,
        bucket_by: Optional[Union["JobBucket", "TagBucket"]] = None,
    ) -> Sequence["RunRecord"]:
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

    # Event Domain
    # ------------

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
    def get_records_for_run(
        self,
        run_id: str,
        cursor: Optional[str] = None,
        of_type: Optional[Union["DagsterEventType", set["DagsterEventType"]]] = None,
        limit: Optional[int] = None,
        ascending: bool = True,
    ) -> "EventLogConnection":
        """Get event records for run.

        NOTE: This method is duplicated here (vs only being in EventMethods) because
        some Datadog tracing spans specifically expect to find this method on the
        DagsterInstance class for proper trace attribution.
        """
        return EventMethods.get_records_for_run(self, run_id, cursor, of_type, limit, ascending)

    # Storage/Partition Domain
    # ------------------------

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
        return self._event_storage.delete_dynamic_partition(partitions_def_name, partition_key)

    @public
    @traced
    def get_dynamic_partitions(self, partitions_def_name: str) -> Sequence[str]:
        """Get the set of partition keys for the specified :py:class:`DynamicPartitionsDefinition`.

        Args:
            partitions_def_name (str): The name of the `DynamicPartitionsDefinition`.
        """
        return self._event_storage.get_dynamic_partitions(partitions_def_name)

    def get_dynamic_partitions_definition_id(self, partitions_def_name: str) -> str:
        from dagster._core.definitions.partitions.context import partition_loading_context
        from dagster._core.definitions.partitions.utils import (
            generate_partition_key_based_definition_id,
        )

        with partition_loading_context() as calling_context:
            dynamic_partitions_store = calling_context.dynamic_partitions_store or self
            # matches the base implementation of the get_serializable_unique_identifier on PartitionsDefinition
            partition_keys = dynamic_partitions_store.get_dynamic_partitions(partitions_def_name)
            return generate_partition_key_based_definition_id(partition_keys)

    @public
    @traced
    def has_dynamic_partition(self, partitions_def_name: str, partition_key: str) -> bool:
        """Check if a partition key exists for the :py:class:`DynamicPartitionsDefinition`.

        Args:
            partitions_def_name (str): The name of the `DynamicPartitionsDefinition`.
            partition_key (str): Partition key to check.
        """
        return self._event_storage.has_dynamic_partition(partitions_def_name, partition_key)

    # =====================================================================================
    # INTERNAL METHODS
    # =====================================================================================

    # Core Instance Methods
    # ---------------------

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
    def defs_state_storage(self) -> Optional["DefsStateStorage"]:
        return self._defs_state_storage

    @property
    def event_log_storage(self) -> "EventLogStorage":
        return self._event_storage

    @property
    def daemon_cursor_storage(self) -> "DaemonCursorStorage":
        return self._run_storage

    @property
    def scheduler(self) -> Optional["Scheduler"]:
        return self._scheduler

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

    def dispose(self) -> None:
        StorageMethods.dispose(self)
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
        from dagster._core.remote_representation.historical import HistoricalJob

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

    # asset storage methods are now in AssetMixin

    # directories

    def __enter__(self) -> Self:
        from dagster._core.storage.defs_state.base import set_defs_state_storage

        self._exit_stack = ExitStack()
        self._exit_stack.enter_context(set_defs_state_storage(self.defs_state_storage))
        return self

    def __exit__(
        self,
        _exception_type: Optional[type[BaseException]],
        _exception_value: Optional[BaseException],
        _traceback: Optional[TracebackType],
    ) -> None:
        self.dispose()
        self._exit_stack.close()

    # backfill

    @property
    def should_start_background_run_thread(self) -> bool:
        """Gate on a feature to start a thread that monitors for if the run should be canceled."""
        return False

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
