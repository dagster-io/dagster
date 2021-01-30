import logging
import os
import sys
import tempfile
import time
import warnings
from collections import defaultdict
from datetime import datetime
from enum import Enum

import yaml
from dagster import check
from dagster.core.definitions.events import AssetKey
from dagster.core.definitions.pipeline import PipelineDefinition, PipelineSubsetDefinition
from dagster.core.errors import (
    DagsterInvariantViolationError,
    DagsterRunAlreadyExists,
    DagsterRunConflict,
)
from dagster.core.storage.migration.utils import upgrading_instance
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.storage.tags import MEMOIZED_RUN_TAG
from dagster.core.system_config.objects import EnvironmentConfig
from dagster.core.utils import str_format_list
from dagster.serdes import ConfigurableClass
from dagster.seven import get_current_datetime_in_utc
from dagster.utils.error import serializable_error_info_from_exc_info

from .config import DAGSTER_CONFIG_YAML_FILENAME
from .ref import InstanceRef

# 'airflow_execution_date' and 'is_airflow_ingest_pipeline' are hardcoded tags used in the
# airflow ingestion logic (see: dagster_pipeline_factory.py). 'airflow_execution_date' stores the
# 'execution_date' used in Airflow operator execution and 'is_airflow_ingest_pipeline' determines
# whether 'airflow_execution_date' is needed.
# https://github.com/dagster-io/dagster/issues/2403
AIRFLOW_EXECUTION_DATE_STR = "airflow_execution_date"
IS_AIRFLOW_INGEST_PIPELINE_STR = "is_airflow_ingest_pipeline"


def _is_dagster_home_set():
    return bool(os.getenv("DAGSTER_HOME"))


def is_memoized_run(tags):
    return tags is not None and MEMOIZED_RUN_TAG in tags and tags.get(MEMOIZED_RUN_TAG) == "true"


def _dagster_home():
    dagster_home_path = os.getenv("DAGSTER_HOME")

    if not dagster_home_path:
        raise DagsterInvariantViolationError(
            (
                "The environment variable $DAGSTER_HOME is not set. Dagster requires this "
                "environment variable to be set to an existing directory in your filesystem "
                "that contains your dagster instance configuration file (dagster.yaml).\n"
                "You can resolve this error by exporting the environment variable."
                "For example, you can run the following command in your shell or "
                "include it in your shell configuration file:\n"
                '\texport DAGSTER_HOME="~/dagster_home"'
            )
        )

    dagster_home_path = os.path.expanduser(dagster_home_path)

    if not os.path.isabs(dagster_home_path):
        raise DagsterInvariantViolationError(
            (
                '$DAGSTER_HOME "{}" must be an absolute path. Dagster requires this '
                "environment variable to be set to an existing directory in your filesystem that"
                "contains your dagster instance configuration file (dagster.yaml)."
            ).format(dagster_home_path)
        )

    if not (os.path.exists(dagster_home_path) and os.path.isdir(dagster_home_path)):
        raise DagsterInvariantViolationError(
            (
                '$DAGSTER_HOME "{}" is not a directory or does not exist. Dagster requires this '
                "environment variable to be set to an existing directory in your filesystem that "
                "contains your dagster instance configuration file (dagster.yaml)."
            ).format(dagster_home_path)
        )

    return dagster_home_path


def _check_run_equality(pipeline_run, candidate_run):
    check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
    check.inst_param(candidate_run, "candidate_run", PipelineRun)

    field_diff = {}
    for field in pipeline_run._fields:
        expected_value = getattr(pipeline_run, field)
        candidate_value = getattr(candidate_run, field)
        if expected_value != candidate_value:
            field_diff[field] = (expected_value, candidate_value)

    return field_diff


def _format_field_diff(field_diff):
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
            for field_name, (expected_value, candidate_value,) in field_diff.items()
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


class DagsterInstance:
    """Core abstraction for managing Dagster's access to storage and other resources.

    Use DagsterInstance.get() to grab the current DagsterInstance which will load based on
    the values in the ``dagster.yaml`` file in ``$DAGSTER_HOME`` if set, otherwise fallback
    to using an ephemeral in-memory set of components.

    Configuration of this class should be done by setting values in ``$DAGSTER_HOME/dagster.yaml``.
    For example, to use Postgres for run and event log storage, you can write a ``dagster.yaml``
    such as the following:

    .. literalinclude:: ../../../../docs/sections/deploying/postgres_dagster.yaml
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
        instance_type,
        local_artifact_storage,
        run_storage,
        event_storage,
        compute_log_manager,
        schedule_storage=None,
        scheduler=None,
        run_coordinator=None,
        run_launcher=None,
        settings=None,
        skip_validation_checks=False,
        ref=None,
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
        self._run_storage = check.inst_param(run_storage, "run_storage", RunStorage)
        self._compute_log_manager = check.inst_param(
            compute_log_manager, "compute_log_manager", ComputeLogManager
        )
        self._schedule_storage = check.opt_inst_param(
            schedule_storage, "schedule_storage", ScheduleStorage
        )
        self._scheduler = check.opt_inst_param(scheduler, "scheduler", Scheduler)

        if self._schedule_storage and not skip_validation_checks:
            self._schedule_storage.validate_stored_schedules(self.scheduler_class)

        self._run_coordinator = check.inst_param(run_coordinator, "run_coordinator", RunCoordinator)
        self._run_coordinator.initialize(self)
        self._run_launcher = check.inst_param(run_launcher, "run_launcher", RunLauncher)
        self._run_launcher.initialize(self)

        self._settings = check.opt_dict_param(settings, "settings")

        self._ref = check.opt_inst_param(ref, "ref", InstanceRef)

        self._subscribers = defaultdict(list)

    # ctors

    @staticmethod
    def ephemeral(tempdir=None, preload=None):
        from dagster.core.run_coordinator import DefaultRunCoordinator
        from dagster.core.launcher.sync_in_memory_run_launcher import SyncInMemoryRunLauncher
        from dagster.core.storage.event_log import InMemoryEventLogStorage
        from dagster.core.storage.root import LocalArtifactStorage
        from dagster.core.storage.runs import InMemoryRunStorage
        from dagster.core.storage.noop_compute_log_manager import NoOpComputeLogManager

        if tempdir is None:
            tempdir = DagsterInstance.temp_storage()

        return DagsterInstance(
            InstanceType.EPHEMERAL,
            local_artifact_storage=LocalArtifactStorage(tempdir),
            run_storage=InMemoryRunStorage(preload=preload),
            event_storage=InMemoryEventLogStorage(preload=preload),
            compute_log_manager=NoOpComputeLogManager(),
            run_coordinator=DefaultRunCoordinator(),
            run_launcher=SyncInMemoryRunLauncher(),
        )

    @staticmethod
    def get(fallback_storage=None):
        # 1. Use $DAGSTER_HOME to determine instance if set.
        if _is_dagster_home_set():
            return DagsterInstance.from_config(_dagster_home())

        # 2. If that is not set use the fallback storage directory if provided.
        # This allows us to have a nice out of the box dagit experience where runs are persisted
        # across restarts in a tempdir that gets cleaned up when the dagit watchdog process exits.
        elif fallback_storage is not None:
            return DagsterInstance.from_config(fallback_storage)

        # 3. If all else fails create an ephemeral in memory instance.
        else:
            return DagsterInstance.ephemeral(fallback_storage)

    @staticmethod
    def get_for_migration():
        return DagsterInstance.from_config(_dagster_home(), skip_validation_checks=True)

    @staticmethod
    def local_temp(tempdir=None, overrides=None):
        warnings.warn(
            "To create a local DagsterInstance for a test, use the instance_for_test "
            "context manager instead, which ensures that resoures are cleaned up afterwards"
        )

        if tempdir is None:
            tempdir = DagsterInstance.temp_storage()

        return DagsterInstance.from_ref(InstanceRef.from_dir(tempdir, overrides=overrides))

    @staticmethod
    def from_config(
        config_dir, config_filename=DAGSTER_CONFIG_YAML_FILENAME, skip_validation_checks=False
    ):
        instance_ref = InstanceRef.from_dir(config_dir, config_filename=config_filename)
        return DagsterInstance.from_ref(instance_ref, skip_validation_checks=skip_validation_checks)

    @staticmethod
    def from_ref(instance_ref, skip_validation_checks=False):
        check.inst_param(instance_ref, "instance_ref", InstanceRef)
        return DagsterInstance(
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
            skip_validation_checks=skip_validation_checks,
            ref=instance_ref,
        )

    # flags

    @property
    def is_persistent(self):
        return self._instance_type == InstanceType.PERSISTENT

    @property
    def is_ephemeral(self):
        return self._instance_type == InstanceType.EPHEMERAL

    def get_ref(self):
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
    def root_directory(self):
        return self._local_artifact_storage.base_dir

    @staticmethod
    def temp_storage():
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

    def info_str(self):
        return yaml.dump(self.info_dict(), default_flow_style=False, sort_keys=False)

    # schedule storage

    @property
    def schedule_storage(self):
        return self._schedule_storage

    # schedule storage

    @property
    def scheduler(self):
        return self._scheduler

    @property
    def scheduler_class(self):
        return self.scheduler.__class__.__name__ if self.scheduler else None

    # run coordinator

    @property
    def run_coordinator(self):
        return self._run_coordinator

    # run launcher

    @property
    def run_launcher(self):
        return self._run_launcher

    # compute logs

    @property
    def compute_log_manager(self):
        return self._compute_log_manager

    def get_settings(self, settings_key):
        check.str_param(settings_key, "settings_key")
        if self._settings and settings_key in self._settings:
            return self._settings.get(settings_key)
        return {}

    @property
    def telemetry_enabled(self):
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

    def upgrade(self, print_fn=lambda _: None):
        with upgrading_instance(self):

            print_fn("Updating run storage...")
            self._run_storage.upgrade()
            self._run_storage.build_missing_indexes()

            print_fn("Updating event storage...")
            self._event_storage.upgrade()

            print_fn("Updating schedule storage...")
            self._schedule_storage.upgrade()

    def optimize_for_dagit(self, statement_timeout):
        self._run_storage.optimize_for_dagit(statement_timeout=statement_timeout)
        self._event_storage.optimize_for_dagit(statement_timeout=statement_timeout)
        if self._schedule_storage:
            self._schedule_storage.optimize_for_dagit(statement_timeout=statement_timeout)

    def reindex(self, print_fn=lambda _: None):
        print_fn("Checking for reindexing...")
        self._event_storage.reindex(print_fn)
        self._run_storage.reindex(print_fn)
        print_fn("Done.")

    def dispose(self):
        self._run_storage.dispose()
        self.run_coordinator.dispose()
        self._run_launcher.dispose()
        self._event_storage.dispose()
        self._compute_log_manager.dispose()

    # run storage

    def get_run_by_id(self, run_id):
        return self._run_storage.get_run_by_id(run_id)

    def get_pipeline_snapshot(self, snapshot_id):
        return self._run_storage.get_pipeline_snapshot(snapshot_id)

    def has_pipeline_snapshot(self, snapshot_id):
        return self._run_storage.has_pipeline_snapshot(snapshot_id)

    def get_historical_pipeline(self, snapshot_id):
        from dagster.core.host_representation import HistoricalPipeline

        snapshot = self._run_storage.get_pipeline_snapshot(snapshot_id)
        parent_snapshot = (
            self._run_storage.get_pipeline_snapshot(snapshot.lineage_snapshot.parent_snapshot_id)
            if snapshot.lineage_snapshot
            else None
        )
        return HistoricalPipeline(
            self._run_storage.get_pipeline_snapshot(snapshot_id), snapshot_id, parent_snapshot
        )

    def has_historical_pipeline(self, snapshot_id):
        return self._run_storage.has_pipeline_snapshot(snapshot_id)

    def get_execution_plan_snapshot(self, snapshot_id):
        return self._run_storage.get_execution_plan_snapshot(snapshot_id)

    def get_run_stats(self, run_id):
        return self._event_storage.get_stats_for_run(run_id)

    def get_run_step_stats(self, run_id, step_keys=None):
        return self._event_storage.get_step_stats_for_run(run_id, step_keys)

    def get_run_tags(self):
        return self._run_storage.get_run_tags()

    def get_run_group(self, run_id):
        return self._run_storage.get_run_group(run_id)

    def create_run_for_pipeline(
        self,
        pipeline_def,
        execution_plan=None,
        run_id=None,
        run_config=None,
        mode=None,
        solids_to_execute=None,
        step_keys_to_execute=None,
        status=None,
        tags=None,
        root_run_id=None,
        parent_run_id=None,
        solid_selection=None,
    ):
        from dagster.core.execution.api import create_execution_plan
        from dagster.core.execution.plan.plan import ExecutionPlan
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

        full_execution_plan = execution_plan or create_execution_plan(
            pipeline_def, run_config=run_config, mode=mode,
        )
        check.invariant(
            len(full_execution_plan.step_keys_to_execute) == len(full_execution_plan.steps)
        )

        if is_memoized_run(tags):
            from dagster.core.execution.resolve_versions import resolve_memoized_execution_plan

            if step_keys_to_execute:
                raise DagsterInvariantViolationError(
                    "step_keys_to_execute parameter cannot be used in conjunction with memoized "
                    "pipeline runs."
                )

            subsetted_execution_plan = resolve_memoized_execution_plan(
                full_execution_plan
            )  # TODO: tighter integration with existing step_keys_to_execute functionality
            step_keys_to_execute = subsetted_execution_plan.step_keys_to_execute
        else:
            subsetted_execution_plan = (
                full_execution_plan.build_subset_plan(step_keys_to_execute)
                if step_keys_to_execute
                else full_execution_plan
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
                subsetted_execution_plan, pipeline_def.get_pipeline_snapshot_id()
            ),
            parent_pipeline_snapshot=pipeline_def.get_parent_pipeline_snapshot(),
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

        return PipelineRun(
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
        check.opt_list_param(step_keys_to_execute, "step_keys_to_execute", of_type=str)

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

        check.invariant(
            set(step_keys_to_execute) == set(execution_plan_snapshot.step_keys_to_execute)
            if step_keys_to_execute
            else set(execution_plan_snapshot.step_keys_to_execute)
            == set([step.key for step in execution_plan_snapshot.steps]),
            "We encode step_keys_to_execute twice in our stack, unfortunately. This check "
            "ensures that they are consistent. We check that step_keys_to_execute in the plan "
            "matches the step_keys_to_execute params if it is set. If it is not, this indicates "
            "a full execution plan, and so we verify that.",
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
                        run_id=pipeline_run.run_id, field_diff=_format_field_diff(field_diff),
                    ),
                )
            return candidate_run

        if self.has_run(pipeline_run.run_id):
            return get_run()

        try:
            return self._run_storage.add_run(pipeline_run)
        except DagsterRunAlreadyExists:
            return get_run()

    def add_run(self, pipeline_run):
        return self._run_storage.add_run(pipeline_run)

    def handle_run_event(self, run_id, event):
        return self._run_storage.handle_run_event(run_id, event)

    def add_run_tags(self, run_id, new_tags):
        return self._run_storage.add_run_tags(run_id, new_tags)

    def has_run(self, run_id):
        return self._run_storage.has_run(run_id)

    def get_runs(self, filters=None, cursor=None, limit=None):
        return self._run_storage.get_runs(filters, cursor, limit)

    def get_runs_count(self, filters=None):
        return self._run_storage.get_runs_count(filters)

    def get_run_groups(self, filters=None, cursor=None, limit=None):
        return self._run_storage.get_run_groups(filters=filters, cursor=cursor, limit=limit)

    def wipe(self):
        self._run_storage.wipe()
        self._event_storage.wipe()

    def delete_run(self, run_id):
        self._run_storage.delete_run(run_id)
        self._event_storage.delete_events(run_id)

    # event storage

    def logs_after(self, run_id, cursor):
        return self._event_storage.get_logs_for_run(run_id, cursor=cursor)

    def all_logs(self, run_id):
        return self._event_storage.get_logs_for_run(run_id)

    def watch_event_logs(self, run_id, cursor, cb):
        return self._event_storage.watch(run_id, cursor, cb)

    # asset storage

    @property
    def is_asset_aware(self):
        return self._event_storage.is_asset_aware

    def check_asset_aware(self):
        check.invariant(
            self.is_asset_aware,
            (
                "Asset queries can only be performed on instances with asset-aware event log "
                "storage. Use `instance.is_asset_aware` to verify that the instance is configured "
                "with an EventLogStorage that implements `AssetAwareEventLogStorage`"
            ),
        )

    def all_asset_keys(self, prefix_path=None):
        self.check_asset_aware()
        return self._event_storage.get_all_asset_keys(prefix_path)

    def has_asset_key(self, asset_key):
        self.check_asset_aware()
        return self._event_storage.has_asset_key(asset_key)

    def events_for_asset_key(
        self,
        asset_key,
        partitions=None,
        before_cursor=None,
        after_cursor=None,
        cursor=None,
        limit=None,
        ascending=False,
    ):
        check.inst_param(asset_key, "asset_key", AssetKey)
        self.check_asset_aware()

        return self._event_storage.get_asset_events(
            asset_key,
            partitions,
            before_cursor,
            after_cursor,
            limit,
            ascending=ascending,
            include_cursor=True,
            cursor=cursor,
        )

    def run_ids_for_asset_key(self, asset_key):
        check.inst_param(asset_key, "asset_key", AssetKey)
        self.check_asset_aware()
        return self._event_storage.get_asset_run_ids(asset_key)

    def wipe_assets(self, asset_keys):
        check.list_param(asset_keys, "asset_keys", of_type=AssetKey)
        self.check_asset_aware()
        for asset_key in asset_keys:
            self._event_storage.wipe_asset(asset_key)

    # event subscriptions

    def get_logger(self):
        logger = logging.Logger("__event_listener")
        logger.addHandler(_EventListenerLogHandler(self))
        logger.setLevel(10)
        return logger

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
        self, message, pipeline_run, engine_event_data=None, cls=None, step_key=None,
    ):
        """
        Report a EngineEvent that occurred outside of a pipeline execution context.
        """
        from dagster.core.events import EngineEventData, DagsterEvent, DagsterEventType
        from dagster.core.events.log import DagsterEventRecord

        check.class_param(cls, "cls")
        check.str_param(message, "message")
        check.inst_param(pipeline_run, "pipeline_run", PipelineRun)
        engine_event_data = check.opt_inst_param(
            engine_event_data, "engine_event_data", EngineEventData, EngineEventData([]),
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
        )
        event_record = DagsterEventRecord(
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
        from dagster.core.events.log import DagsterEventRecord

        check.inst_param(run, "run", PipelineRun)
        message = check.opt_str_param(message, "message", "Sending pipeline termination request.",)
        canceling_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_CANCELING.value,
            pipeline_name=run.pipeline_name,
            message=message,
        )

        event_record = DagsterEventRecord(
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
        self, pipeline_run, message=None,
    ):
        from dagster.core.events import DagsterEvent, DagsterEventType
        from dagster.core.events.log import DagsterEventRecord

        check.inst_param(pipeline_run, "pipeline_run", PipelineRun)

        message = check.opt_str_param(
            message,
            "mesage",
            "This pipeline run has been marked as canceled from outside the execution context.",
        )

        dagster_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_CANCELED.value,
            pipeline_name=pipeline_run.pipeline_name,
            message=message,
        )
        event_record = DagsterEventRecord(
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
        from dagster.core.events.log import DagsterEventRecord

        check.inst_param(pipeline_run, "pipeline_run", PipelineRun)

        message = check.opt_str_param(
            message,
            "message",
            "This pipeline run has been marked as failed from outside the execution context.",
        )

        dagster_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_FAILURE.value,
            pipeline_name=pipeline_run.pipeline_name,
            message=message,
        )
        event_record = DagsterEventRecord(
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

    def intermediates_directory(self, run_id):
        return self._local_artifact_storage.intermediates_dir(run_id)

    def schedules_directory(self):
        return self._local_artifact_storage.schedules_dir

    # Runs coordinator

    def submit_run(self, run_id, external_pipeline):
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

        run = self.get_run_by_id(run_id)
        check.inst(
            run.external_pipeline_origin,
            ExternalPipelineOrigin,
            "External pipeline origin must be set for submitted runs",
        )

        try:
            submitted_run = self._run_coordinator.submit_run(
                run, external_pipeline=external_pipeline
            )
        except:
            from dagster.core.events import EngineEventData

            error = serializable_error_info_from_exc_info(sys.exc_info())
            self.report_engine_event(
                error.message, run, EngineEventData.engine_error(error),
            )
            self.report_run_failed(run)
            raise

        return submitted_run

    # Run launcher

    def launch_run(self, run_id, external_pipeline):
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
        run = self.get_run_by_id(run_id)

        from dagster.core.events import EngineEventData, DagsterEvent, DagsterEventType
        from dagster.core.events.log import DagsterEventRecord

        launch_started_event = DagsterEvent(
            event_type_value=DagsterEventType.PIPELINE_STARTING.value,
            pipeline_name=run.pipeline_name,
        )

        event_record = DagsterEventRecord(
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

        try:
            self._run_launcher.launch_run(self, run, external_pipeline=external_pipeline)
        except:
            error = serializable_error_info_from_exc_info(sys.exc_info())
            self.report_engine_event(
                error.message, run, EngineEventData.engine_error(error),
            )
            self.report_run_failed(run)
            raise

        return run

    # Scheduler

    def reconcile_scheduler_state(self, external_repository):
        return self._scheduler.reconcile_scheduler_state(self, external_repository)

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
        from dagster.core.definitions.job import JobType
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
        from dagster.core.definitions.job import JobType

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
            # set the last completed time to the modified state time
            self.update_job_state(
                job_state.with_status(JobStatus.RUNNING).with_data(
                    SensorJobData(
                        last_tick_timestamp=datetime.utcnow().timestamp(),
                        min_interval=external_sensor.min_interval_seconds,
                    )
                )
            )

    def stop_sensor(self, job_origin_id):
        from dagster.core.scheduler.job import JobStatus, SensorJobData

        job_state = self.get_job_state(job_origin_id)
        if job_state:
            self.update_job_state(
                job_state.with_status(JobStatus.STOPPED).with_data(
                    SensorJobData(datetime.utcnow().timestamp())
                )
            )

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
    def add_daemon_heartbeat(self, daemon_heartbeat):
        """Called on a regular interval by the daemon"""
        self._run_storage.add_daemon_heartbeat(daemon_heartbeat)

    def get_daemon_heartbeats(self):
        """Latest heartbeats of all daemon types"""
        return self._run_storage.get_daemon_heartbeats()

    def wipe_daemon_heartbeats(self):
        self._run_storage.wipe_daemon_heartbeats()
