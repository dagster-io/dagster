import logging
import sys
from collections import defaultdict
from types import TracebackType
from typing import Dict, Optional, Sequence, Tuple, Type

import pendulum

import dagster._check as check
from dagster._core.definitions.asset_daemon_context import AssetDaemonContext
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.external_asset_graph import ExternalAssetGraph
from dagster._core.definitions.run_request import (
    InstigatorType,
    RunRequest,
)
from dagster._core.definitions.selector import JobSubsetSelector
from dagster._core.errors import (
    DagsterCodeLocationLoadError,
    DagsterUserCodeUnreachableError,
)
from dagster._core.host_representation.external import (
    ExternalExecutionPlan,
    ExternalJob,
)
from dagster._core.instance import DagsterInstance
from dagster._core.scheduler.instigation import (
    InstigatorTick,
    TickData,
    TickStatus,
)
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.storage.tags import (
    ASSET_EVALUATION_ID_TAG,
    AUTO_MATERIALIZE_TAG,
    AUTO_OBSERVE_TAG,
)
from dagster._core.utils import make_new_run_id
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._core.workspace.workspace import IWorkspace
from dagster._daemon.daemon import DaemonIterator, IntervalDaemon
from dagster._utils import (
    SingleInstigatorDebugCrashFlags,
    check_for_debug_crash,
    hash_collection,
)
from dagster._utils.error import serializable_error_info_from_exc_info

CURSOR_KEY = "ASSET_DAEMON_CURSOR"
ASSET_DAEMON_PAUSED_KEY = "ASSET_DAEMON_PAUSED"

EVALUATIONS_TTL_DAYS = 30

# When retrying a tick, how long to wait before ignoring it and moving on to the next one
# (To account for the rare case where the daemon is down for a long time, starts back up, and
# there's an old in-progress tick left to finish that may no longer be correct to finish)
MAX_TIME_TO_RESUME_TICK_SECONDS = 60 * 60 * 24

FIXED_AUTO_MATERIALIZATION_ORIGIN_ID = "asset_daemon_origin"
FIXED_AUTO_MATERIALIZATION_SELECTOR_ID = "asset_daemon_selector"
FIXED_AUTO_MATERIALIZATION_INSTIGATOR_NAME = "asset_daemon"


def get_auto_materialize_paused(instance: DagsterInstance) -> bool:
    return (
        instance.daemon_cursor_storage.get_cursor_values({ASSET_DAEMON_PAUSED_KEY}).get(
            ASSET_DAEMON_PAUSED_KEY
        )
        != "false"
    )


def set_auto_materialize_paused(instance: DagsterInstance, paused: bool):
    instance.daemon_cursor_storage.set_cursor_values(
        {ASSET_DAEMON_PAUSED_KEY: "true" if paused else "false"}
    )


def _get_raw_cursor(instance: DagsterInstance) -> Optional[str]:
    return instance.daemon_cursor_storage.get_cursor_values({CURSOR_KEY}).get(CURSOR_KEY)


def get_current_evaluation_id(instance: DagsterInstance) -> Optional[int]:
    raw_cursor = _get_raw_cursor(instance)
    return AssetDaemonCursor.get_evaluation_id_from_serialized(raw_cursor) if raw_cursor else None


class AutoMaterializeLaunchContext:
    def __init__(
        self,
        tick: InstigatorTick,
        instance: DagsterInstance,
        logger: logging.Logger,
        tick_retention_settings,
    ):
        self._tick = tick
        self._logger = logger
        self._instance = instance

        self._purge_settings = defaultdict(set)
        for status, day_offset in tick_retention_settings.items():
            self._purge_settings[day_offset].add(status)

    @property
    def status(self) -> TickStatus:
        return self._tick.status

    @property
    def tick(self) -> InstigatorTick:
        return self._tick

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    def add_run_info(self, run_id=None):
        self._tick = self._tick.with_run_info(run_id)

    def set_run_requests(
        self,
        run_requests: Sequence[RunRequest],
        reserved_run_ids: Optional[Sequence[str]],
    ):
        self._tick = self._tick.with_run_requests(run_requests, reserved_run_ids=reserved_run_ids)
        return self._tick

    def update_state(self, status: TickStatus, **kwargs: object):
        self._tick = self._tick.with_status(status=status, **kwargs)

    def __enter__(self):
        return self

    def __exit__(
        self,
        exception_type: Type[BaseException],
        exception_value: Exception,
        traceback: TracebackType,
    ) -> None:
        if exception_value and isinstance(exception_value, KeyboardInterrupt):
            return

        # Log the error if the failure wasn't an interrupt or the daemon generator stopping
        if exception_value and not isinstance(exception_value, GeneratorExit):
            if isinstance(
                exception_value, (DagsterUserCodeUnreachableError, DagsterCodeLocationLoadError)
            ):
                try:
                    raise Exception(
                        "Unable to reach the code server. Auto-materialization will resume once the code server is available."
                    ) from exception_value
                except:
                    error_data = serializable_error_info_from_exc_info(sys.exc_info())
                    self._logger.exception("Auto-materialize daemon caught an error")
                    self.update_state(
                        TickStatus.FAILURE,
                        error=error_data,
                        # don't increment the failure count - retry until the server is available again
                        failure_count=self._tick.failure_count,
                    )
            else:
                error_data = serializable_error_info_from_exc_info(sys.exc_info())
                self._logger.exception("Auto-materialize daemon caught an error")
                self.update_state(
                    TickStatus.FAILURE, error=error_data, failure_count=self._tick.failure_count + 1
                )

        check.invariant(
            self._tick.status != TickStatus.STARTED,
            "Tick must be in a terminal state when the AutoMaterializeLaunchContext is closed",
        )

        # write the new tick status to the database

        self.write()

        for day_offset, statuses in self._purge_settings.items():
            if day_offset <= 0:
                continue
            self._instance.purge_ticks(
                FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
                FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
                before=pendulum.now("UTC").subtract(days=day_offset).timestamp(),
                tick_statuses=list(statuses),
            )

    def write(self) -> None:
        self._instance.update_tick(self._tick)


class AssetDaemon(IntervalDaemon):
    def __init__(self, interval_seconds: int):
        super().__init__(interval_seconds=interval_seconds)

    @classmethod
    def daemon_type(cls) -> str:
        return "ASSET"

    def run_iteration(
        self,
        workspace_process_context: IWorkspaceProcessContext,
    ) -> DaemonIterator:
        yield from self._run_iteration_impl(
            workspace_process_context,
            debug_crash_flags={},
        )

    def _run_iteration_impl(
        self,
        workspace_process_context: IWorkspaceProcessContext,
        debug_crash_flags: SingleInstigatorDebugCrashFlags,
    ) -> DaemonIterator:
        instance = workspace_process_context.instance

        if get_auto_materialize_paused(instance):
            yield
            return

        schedule_storage = check.not_none(
            instance.schedule_storage,
            "Auto materialization requires schedule storage to be configured",
        )

        if not schedule_storage.supports_auto_materialize_asset_evaluations:
            self._logger.warning(
                "Auto materialize evaluations are not getting logged. Run `dagster instance"
                " migrate` to enable."
            )

        evaluation_time = pendulum.now("UTC")

        workspace = workspace_process_context.create_request_context()
        asset_graph = ExternalAssetGraph.from_workspace(workspace)
        target_asset_keys = {
            target_key
            for target_key in asset_graph.materializable_asset_keys
            if asset_graph.get_auto_materialize_policy(target_key) is not None
        }
        num_target_assets = len(target_asset_keys)

        auto_observe_assets = [
            key
            for key in asset_graph.source_asset_keys
            if asset_graph.get_auto_observe_interval_minutes(key) is not None
        ]

        num_auto_observe_assets = len(auto_observe_assets)
        has_auto_observe_assets = any(auto_observe_assets)

        if not target_asset_keys and not has_auto_observe_assets:
            self._logger.debug("No assets that require auto-materialize checks")
            yield
            return

        self._logger.info(
            f"Checking {num_target_assets} asset{'' if num_target_assets == 1 else 's'} and"
            f" {num_auto_observe_assets} observable source"
            f" asset{'' if num_auto_observe_assets == 1 else 's'} for auto-materialization"
        )

        raw_cursor = _get_raw_cursor(instance)
        stored_cursor = (
            AssetDaemonCursor.from_serialized(raw_cursor, asset_graph)
            if raw_cursor
            else AssetDaemonCursor.empty()
        )

        tick_retention_settings = instance.get_tick_retention_settings(
            InstigatorType.AUTO_MATERIALIZE
        )

        ticks = instance.get_ticks(
            FIXED_AUTO_MATERIALIZATION_ORIGIN_ID, FIXED_AUTO_MATERIALIZATION_SELECTOR_ID, limit=1
        )
        latest_tick = ticks[0] if ticks else None

        max_retries = instance.auto_materialize_max_tick_retries

        # Determine if the most recent tick requires retrying
        retry_tick: Optional[InstigatorTick] = None

        if latest_tick:
            # If the previous tick matches the stored cursor's evaluation ID, check if it failed
            # or crashed partway through execution and needs to be resumed
            # Don't resume very old ticks though in case the daemon crashed for a long time and
            # then restarted
            if (
                pendulum.now("UTC").timestamp() - latest_tick.timestamp
                <= MAX_TIME_TO_RESUME_TICK_SECONDS
                and latest_tick.tick_data.auto_materialize_evaluation_id
                == stored_cursor.evaluation_id
            ):
                if latest_tick.status == TickStatus.STARTED:
                    self._logger.warn(
                        f"Tick for evaluation {stored_cursor.evaluation_id} was interrupted part-way through, resuming"
                    )
                    retry_tick = latest_tick
                elif (
                    latest_tick.status == TickStatus.FAILURE
                    and latest_tick.tick_data.failure_count <= max_retries
                ):
                    self._logger.info(
                        f"Retrying failed tick for evaluation {stored_cursor.evaluation_id}"
                    )
                    retry_tick = instance.create_tick(
                        latest_tick.tick_data.with_status(
                            TickStatus.STARTED,
                            error=None,
                            timestamp=evaluation_time.timestamp(),
                            end_timestamp=None,
                        ),
                    )
            else:
                # (The evaluation IDs not matching indicates that the tick failed or crashed before
                # the cursor could be written, so no runs have been launched and it's safe to
                # re-evaluate things from scratch in a new tick without retrying anything)
                if latest_tick.status == TickStatus.STARTED:
                    # Old tick that won't be resumed - move it into a SKIPPED state so it isn't
                    # left dangling in STARTED
                    self._logger.warn(
                        f"Moving dangling STARTED tick from evaluation {latest_tick.tick_data.auto_materialize_evaluation_id} into SKIPPED"
                    )
                    latest_tick = latest_tick.with_status(status=TickStatus.SKIPPED)
                    instance.update_tick(latest_tick)

        if retry_tick:
            tick = retry_tick
        else:
            tick = instance.create_tick(
                TickData(
                    instigator_origin_id=FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
                    instigator_name=FIXED_AUTO_MATERIALIZATION_INSTIGATOR_NAME,
                    instigator_type=InstigatorType.AUTO_MATERIALIZE,
                    status=TickStatus.STARTED,
                    timestamp=evaluation_time.timestamp(),
                    selector_id=FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
                    auto_materialize_evaluation_id=stored_cursor.evaluation_id + 1,
                )
            )

        evaluation_id = check.not_none(tick.tick_data.auto_materialize_evaluation_id)

        with AutoMaterializeLaunchContext(
            tick,
            instance,
            self._logger,
            tick_retention_settings,
        ) as tick_context:
            if retry_tick:
                # Unfinished or retried tick already generated evaluations and run requests and cursor, now
                # need to finish it
                run_requests = tick.tick_data.run_requests or []
                reserved_run_ids = tick.tick_data.reserved_run_ids or []

                if schedule_storage.supports_auto_materialize_asset_evaluations:
                    evaluation_records = (
                        schedule_storage.get_auto_materialize_evaluations_for_evaluation_id(
                            evaluation_id
                        )
                    )
                    evaluations_by_asset_key = {
                        evaluation_record.asset_key: evaluation_record.evaluation
                        for evaluation_record in evaluation_records
                    }
                else:
                    evaluations_by_asset_key = {}
            else:
                run_requests, new_cursor, evaluations = AssetDaemonContext(
                    asset_graph=asset_graph,
                    target_asset_keys=target_asset_keys,
                    instance=instance,
                    cursor=stored_cursor,
                    materialize_run_tags={
                        **instance.auto_materialize_run_tags,
                    },
                    observe_run_tags={AUTO_OBSERVE_TAG: "true"},
                    auto_observe=True,
                    respect_materialization_data_versions=instance.auto_materialize_respect_materialization_data_versions,
                    logger=self._logger,
                ).evaluate()

                check.invariant(new_cursor.evaluation_id == evaluation_id)

                check_for_debug_crash(debug_crash_flags, "EVALUATIONS_FINISHED")

                evaluations_by_asset_key = {
                    evaluation.asset_key: evaluation for evaluation in evaluations
                }

                # Write the asset evaluations without run IDs first
                if schedule_storage.supports_auto_materialize_asset_evaluations:
                    schedule_storage.add_auto_materialize_asset_evaluations(
                        evaluation_id, list(evaluations_by_asset_key.values())
                    )
                    check_for_debug_crash(debug_crash_flags, "ASSET_EVALUATIONS_ADDED")

                reserved_run_ids = [make_new_run_id() for _ in range(len(run_requests))]

                # Write out the in-progress tick data, which ensures that if the tick crashes or raises an exception, it will retry
                tick = tick_context.set_run_requests(
                    run_requests=run_requests,
                    reserved_run_ids=reserved_run_ids,
                )
                tick_context.write()
                check_for_debug_crash(debug_crash_flags, "RUN_REQUESTS_CREATED")

                # Write out the persistent cursor, which ensures that future ticks will move on once
                # they determine that nothing needs to be retried
                instance.daemon_cursor_storage.set_cursor_values(
                    {CURSOR_KEY: new_cursor.serialize()}
                )

                check_for_debug_crash(debug_crash_flags, "CURSOR_UPDATED")

            self._logger.info(
                "Tick produced"
                f" {len(run_requests)} run{'s' if len(run_requests) != 1 else ''} and"
                f" {len(evaluations_by_asset_key)} asset"
                f" evaluation{'s' if len(evaluations_by_asset_key) != 1 else ''} for evaluation ID"
                f" {evaluation_id}"
            )

            pipeline_and_execution_plan_cache: Dict[
                int, Tuple[ExternalJob, ExternalExecutionPlan]
            ] = {}

            check.invariant(len(run_requests) == len(reserved_run_ids))

            updated_evaluation_asset_keys = set()

            for i in range(len(run_requests)):
                reserved_run_id = reserved_run_ids[i]
                run_request = run_requests[i]

                asset_keys = check.not_none(run_request.asset_selection)

                submitted_run = submit_asset_run(
                    reserved_run_id,
                    run_request._replace(
                        tags={
                            **run_request.tags,
                            AUTO_MATERIALIZE_TAG: "true",
                            ASSET_EVALUATION_ID_TAG: str(evaluation_id),
                        }
                    ),
                    instance,
                    workspace,
                    asset_graph,
                    pipeline_and_execution_plan_cache,
                    self._logger,
                    debug_crash_flags,
                    i,
                )

                tick_context.add_run_info(run_id=submitted_run.run_id)

                # write the submitted run ID to any evaluations
                for asset_key in asset_keys:
                    # asset keys for observation runs don't have evaluations
                    if asset_key in evaluations_by_asset_key:
                        evaluation = evaluations_by_asset_key[asset_key]
                        evaluations_by_asset_key[asset_key] = evaluation._replace(
                            run_ids=evaluation.run_ids | {submitted_run.run_id}
                        )
                        updated_evaluation_asset_keys.add(asset_key)

            evaluations_to_update = [
                evaluations_by_asset_key[asset_key] for asset_key in updated_evaluation_asset_keys
            ]
            if evaluations_to_update:
                schedule_storage.add_auto_materialize_asset_evaluations(
                    evaluation_id, evaluations_to_update
                )

            check_for_debug_crash(debug_crash_flags, "RUN_IDS_ADDED_TO_EVALUATIONS")

            tick_context.update_state(
                TickStatus.SUCCESS if len(run_requests) > 0 else TickStatus.SKIPPED,
            )

        if schedule_storage.supports_auto_materialize_asset_evaluations:
            schedule_storage.purge_asset_evaluations(
                before=pendulum.now("UTC").subtract(days=EVALUATIONS_TTL_DAYS).timestamp(),
            )

        self._logger.info("Finished auto-materialization tick")


def submit_asset_run(
    run_id: str,
    run_request: RunRequest,
    instance: DagsterInstance,
    workspace: IWorkspace,
    asset_graph: ExternalAssetGraph,
    pipeline_and_execution_plan_cache: Dict[int, Tuple[ExternalJob, ExternalExecutionPlan]],
    logger: logging.Logger,
    debug_crash_flags: SingleInstigatorDebugCrashFlags,
    run_request_index: int,
) -> DagsterRun:
    check.invariant(
        not run_request.run_config, "Asset materialization run requests have no custom run config"
    )
    asset_keys = check.not_none(run_request.asset_selection)

    check.invariant(len(asset_keys) > 0)

    # check if the run already exists

    run_to_submit = None

    existing_run = instance.get_run_by_id(run_id)
    if existing_run:
        if existing_run.status != DagsterRunStatus.NOT_STARTED:
            logger.warn(
                f"Run {run_id} already submitted on a previously interrupted tick, skipping"
            )

            check_for_debug_crash(debug_crash_flags, "RUN_SUBMITTED")
            check_for_debug_crash(debug_crash_flags, f"RUN_SUBMITTED_{run_request_index}")

            return existing_run
        else:
            logger.warn(
                f"Run {run_id} already created on a previously interrupted tick, submitting"
            )
            run_to_submit = existing_run

    if not run_to_submit:
        repo_handle = asset_graph.get_repository_handle(asset_keys[0])

        # Check that all asset keys are from the same repo
        for key in asset_keys[1:]:
            check.invariant(repo_handle == asset_graph.get_repository_handle(key))

        location_name = repo_handle.code_location_origin.location_name
        repository_name = repo_handle.repository_name
        code_location = workspace.get_code_location(location_name)
        job_name = check.not_none(
            asset_graph.get_implicit_job_name_for_assets(
                asset_keys, code_location.get_repository(repository_name)
            )
        )

        job_selector = JobSubsetSelector(
            location_name=location_name,
            repository_name=repository_name,
            job_name=job_name,
            op_selection=None,
            asset_selection=asset_keys,
        )

        selector_id = hash_collection(job_selector)

        if selector_id not in pipeline_and_execution_plan_cache:
            external_job = code_location.get_external_job(job_selector)

            external_execution_plan = code_location.get_external_execution_plan(
                external_job,
                run_config={},
                step_keys_to_execute=None,
                known_state=None,
                instance=instance,
            )
            pipeline_and_execution_plan_cache[selector_id] = (
                external_job,
                external_execution_plan,
            )

        check_for_debug_crash(debug_crash_flags, "EXECUTION_PLAN_CREATED")
        check_for_debug_crash(debug_crash_flags, f"EXECUTION_PLAN_CREATED_{run_request_index}")

        external_job, external_execution_plan = pipeline_and_execution_plan_cache[selector_id]

        execution_plan_snapshot = external_execution_plan.execution_plan_snapshot

        run_to_submit = instance.create_run(
            job_name=external_job.name,
            run_id=run_id,
            run_config=None,
            resolved_op_selection=None,
            step_keys_to_execute=None,
            status=DagsterRunStatus.NOT_STARTED,
            op_selection=None,
            root_run_id=None,
            parent_run_id=None,
            tags=run_request.tags,
            job_snapshot=external_job.job_snapshot,
            execution_plan_snapshot=execution_plan_snapshot,
            parent_job_snapshot=external_job.parent_job_snapshot,
            external_job_origin=external_job.get_external_origin(),
            job_code_origin=external_job.get_python_origin(),
            asset_selection=frozenset(asset_keys),
            asset_check_selection=None,
        )

    check_for_debug_crash(debug_crash_flags, "RUN_CREATED")
    check_for_debug_crash(debug_crash_flags, f"RUN_CREATED_{run_request_index}")

    instance.submit_run(run_to_submit.run_id, workspace)

    check_for_debug_crash(debug_crash_flags, "RUN_SUBMITTED")
    check_for_debug_crash(debug_crash_flags, f"RUN_SUBMITTED_{run_request_index}")

    asset_key_str = ", ".join([asset_key.to_user_string() for asset_key in asset_keys])

    logger.info(
        f"Submitted run {run_to_submit.run_id} for assets {asset_key_str} with tags"
        f" {run_request.tags}"
    )

    return run_to_submit
