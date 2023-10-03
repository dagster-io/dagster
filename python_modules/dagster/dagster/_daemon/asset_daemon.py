import logging
import sys
from collections import defaultdict
from types import TracebackType
from typing import (
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
)

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
from dagster._core.storage.dagster_run import DagsterRunStatus
from dagster._core.storage.tags import (
    ASSET_EVALUATION_ID_TAG,
    AUTO_MATERIALIZE_TAG,
    AUTO_OBSERVE_TAG,
)
from dagster._core.workspace.context import IWorkspaceProcessContext
from dagster._core.workspace.workspace import IWorkspace
from dagster._daemon.daemon import DaemonIterator, IntervalDaemon
from dagster._utils import hash_collection
from dagster._utils.error import serializable_error_info_from_exc_info

CURSOR_KEY = "ASSET_DAEMON_CURSOR"
ASSET_DAEMON_PAUSED_KEY = "ASSET_DAEMON_PAUSED"

EVALUATIONS_TTL_DAYS = 30

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
    def logger(self) -> logging.Logger:
        return self._logger

    def add_run_info(self, run_id=None):
        self._tick = self._tick.with_run_info(run_id)

    def set_run_requests(self, run_requests: Sequence[RunRequest]):
        self._tick = self._tick.with_run_requests(run_requests)

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
            error_data = serializable_error_info_from_exc_info(sys.exc_info())
            tick_finish_timestamp = pendulum.now("UTC").timestamp()
            self.update_state(
                TickStatus.FAILURE, error=error_data, end_timestamp=tick_finish_timestamp
            )

        self._write()

        for day_offset, statuses in self._purge_settings.items():
            if day_offset <= 0:
                continue
            self._instance.purge_ticks(
                FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
                FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
                before=pendulum.now("UTC").subtract(days=day_offset).timestamp(),
                tick_statuses=list(statuses),
            )

    def _write(self) -> None:
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
        cursor = (
            AssetDaemonCursor.from_serialized(raw_cursor, asset_graph)
            if raw_cursor
            else AssetDaemonCursor.empty()
        )

        tick_retention_settings = instance.get_tick_retention_settings(
            InstigatorType.AUTO_MATERIALIZE
        )

        evaluation_id = cursor.evaluation_id + 1

        tick = instance.create_tick(
            TickData(
                instigator_origin_id=FIXED_AUTO_MATERIALIZATION_ORIGIN_ID,
                instigator_name=FIXED_AUTO_MATERIALIZATION_INSTIGATOR_NAME,
                instigator_type=InstigatorType.AUTO_MATERIALIZE,
                status=TickStatus.STARTED,
                timestamp=evaluation_time.timestamp(),
                selector_id=FIXED_AUTO_MATERIALIZATION_SELECTOR_ID,
                auto_materialize_evaluation_id=evaluation_id,
            )
        )

        with AutoMaterializeLaunchContext(
            tick, instance, self._logger, tick_retention_settings
        ) as tick_context:
            run_requests, new_cursor, evaluations = AssetDaemonContext(
                asset_graph=asset_graph,
                target_asset_keys=target_asset_keys,
                instance=instance,
                cursor=cursor,
                materialize_run_tags={
                    **instance.auto_materialize_run_tags,
                },
                observe_run_tags={AUTO_OBSERVE_TAG: "true"},
                auto_observe=True,
                respect_materialization_data_versions=instance.auto_materialize_respect_materialization_data_versions,
                logger=self._logger,
            ).evaluate()

            self._logger.info(
                f"Tick produced {len(run_requests)} run{'s' if len(run_requests) != 1 else ''} and"
                f" {len(evaluations)} asset evaluation{'s' if len(evaluations) != 1 else ''} for"
                f" evaluation ID {new_cursor.evaluation_id}"
            )

            evaluations_by_asset_key = {
                evaluation.asset_key: evaluation for evaluation in evaluations
            }

            pipeline_and_execution_plan_cache: Dict[
                int, Tuple[ExternalJob, ExternalExecutionPlan]
            ] = {}

            submit_job_inputs: List[Tuple[RunRequest, ExternalJob, ExternalExecutionPlan]] = []

            # First do work that is most likely to fail before doing any writes (to make
            # double-creation of runs less likely)
            for run_request in run_requests:
                yield
                submit_job_inputs.append(
                    get_asset_run_submit_input(
                        run_request._replace(
                            tags={
                                **run_request.tags,
                                AUTO_MATERIALIZE_TAG: "true",
                                ASSET_EVALUATION_ID_TAG: str(new_cursor.evaluation_id),
                            }
                        ),
                        instance,
                        workspace,
                        asset_graph,
                        pipeline_and_execution_plan_cache,
                    )
                )

            tick_context.set_run_requests(run_requests=run_requests)

            # Now submit all runs to the queue
            for submit_job_input in submit_job_inputs:
                yield

                run_request, external_job, external_execution_plan = submit_job_input

                asset_keys = check.not_none(run_request.asset_selection)

                run = submit_asset_run(
                    run_request, instance, workspace, external_job, external_execution_plan
                )

                asset_key_str = ", ".join([asset_key.to_user_string() for asset_key in asset_keys])

                self._logger.info(
                    f"Launched run {run.run_id} for assets {asset_key_str} with tags"
                    f" {run_request.tags}"
                )

                tick_context.add_run_info(run_id=run.run_id)

                # add run id to evaluations
                for asset_key in asset_keys:
                    # asset keys for observation runs don't have evaluations
                    if asset_key in evaluations_by_asset_key:
                        evaluation = evaluations_by_asset_key[asset_key]
                        evaluations_by_asset_key[asset_key] = evaluation._replace(
                            run_ids=evaluation.run_ids | {run.run_id}
                        )

            tick_finish_timestamp = pendulum.now("UTC").timestamp()

            instance.daemon_cursor_storage.set_cursor_values({CURSOR_KEY: new_cursor.serialize()})
            tick_context.update_state(
                TickStatus.SUCCESS if len(run_requests) > 0 else TickStatus.SKIPPED,
                end_timestamp=tick_finish_timestamp,
            )

        # We enforce uniqueness per (asset key, evaluation id). Store the evaluations after the cursor,
        # so that if the daemon crashes and doesn't update the cursor we don't try to write duplicates.
        if schedule_storage.supports_auto_materialize_asset_evaluations:
            schedule_storage.add_auto_materialize_asset_evaluations(
                new_cursor.evaluation_id, list(evaluations_by_asset_key.values())
            )
            schedule_storage.purge_asset_evaluations(
                before=pendulum.now("UTC").subtract(days=EVALUATIONS_TTL_DAYS).timestamp(),
            )

        self._logger.info("Finished auto-materialization tick")


def get_asset_run_submit_input(
    run_request: RunRequest,
    instance: DagsterInstance,
    workspace: IWorkspace,
    asset_graph: ExternalAssetGraph,
    pipeline_and_execution_plan_cache: Dict[int, Tuple[ExternalJob, ExternalExecutionPlan]] = {},
) -> Tuple[RunRequest, ExternalJob, ExternalExecutionPlan]:
    check.invariant(
        not run_request.run_config, "Asset materialization run requests have no custom run config"
    )

    asset_keys = check.not_none(run_request.asset_selection)
    check.invariant(len(asset_keys) > 0)

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

    external_job, external_execution_plan = pipeline_and_execution_plan_cache[selector_id]

    return (run_request, external_job, external_execution_plan)


def submit_asset_run(
    run_request: RunRequest,
    instance: DagsterInstance,
    workspace: IWorkspace,
    external_job: ExternalJob,
    external_execution_plan: ExternalExecutionPlan,
):
    asset_keys = check.not_none(run_request.asset_selection)

    execution_plan_snapshot = external_execution_plan.execution_plan_snapshot

    run = instance.create_run(
        job_name=external_job.name,
        run_id=None,
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
    instance.submit_run(run.run_id, workspace)
    return run
