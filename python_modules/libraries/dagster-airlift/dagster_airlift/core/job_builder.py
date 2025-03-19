import ast
import os
import sys
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import ExitStack
from datetime import timedelta
from typing import Callable, Optional, Union, cast

import dagster as dg
from dagster import _check as check
from dagster._core.definitions import Failure, RetryRequested
from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.input import InputMapping
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.output import OutputMapping
from dagster._core.definitions.run_request import RunRequest
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition
from dagster._core.errors import (
    DagsterError,
    DagsterExecutionInterruptedError,
    DagsterMaxRetriesExceededError,
    DagsterUserCodeExecutionError,
)
from dagster._core.events import DagsterEvent, EngineEventData
from dagster._core.execution.api import ExecuteRunWithPlanIterable
from dagster._core.execution.compute_logs import create_compute_log_file_key
from dagster._core.execution.context.system import (
    PlanExecutionContext,
    PlanOrchestrationContext,
    StepExecutionContext,
)
from dagster._core.execution.context_creation_job import PlanExecutionContextManager
from dagster._core.execution.plan.execute_step import core_dagster_event_sequence_for_step
from dagster._core.execution.plan.instance_concurrency_context import InstanceConcurrencyContext
from dagster._core.execution.plan.objects import (
    ErrorSource,
    StepFailureData,
    StepRetryData,
    UserFailureData,
    step_failure_event_from_exc_info,
)
from dagster._core.execution.plan.plan import ExecutionPlan
from dagster._core.execution.retries import RetryMode
from dagster._core.storage.tags import KIND_PREFIX
from dagster._grpc.client import DEFAULT_SENSOR_GRPC_TIMEOUT
from dagster._serdes.serdes import deserialize_value, serialize_value, whitelist_for_serdes
from dagster._time import datetime_from_timestamp, get_current_datetime
from dagster._utils.error import SerializableErrorInfo, serializable_error_info_from_exc_info
from dagster._utils.timing import format_duration, time_execution_scope
from dagster_shared.record import record

from dagster_airlift.core.airflow_instance import AirflowInstance, Dataset
from dagster_airlift.core.top_level_dag_def_api import assets_with_dag_mappings


def parse_af_log_response(logs: str) -> list:
    parsed_data: list = ast.literal_eval(logs)
    return parsed_data


def make_key_from_dataset_uri(uri: str) -> dg.AssetKey:
    sanitized_uri = uri.replace("s3://", "").replace("/", "_").replace(".", "_")
    return dg.AssetKey(sanitized_uri)


def make_dataset_spec(dataset: Dataset, upstreams: list[str]) -> dg.AssetSpec:
    kinds = ["airflow"]
    if dataset.uri.startswith("s3://"):
        kinds.append("s3")
    if dataset.uri.endswith(".csv"):
        kinds.append("csv")
    # For now; we're only mapping at the dag level to keep things easy. A real version of this
    # Would need to do complicated task level mapping which interstitially adds metadata to the
    # assets.
    if upstreams:
        print(f"UPSTREAMS: {upstreams}")
    return assets_with_dag_mappings(
        # In general we'll need to support more than one.
        {
            dataset.producing_tasks[0].dag_id: [
                dg.AssetSpec(
                    key=make_key_from_dataset_uri(dataset.uri),
                    metadata={"uri": dataset.uri},
                    kinds=set(kinds),
                    deps=[make_key_from_dataset_uri(upstream) for upstream in upstreams],
                )
            ]
        }
    )[0]


def make_output_name_from_key(key: dg.AssetKey) -> str:
    joined_path = "_".join(key.path)
    return f"{joined_path}_out".replace("-", "_")


def make_input_name_from_key(key: dg.AssetKey) -> str:
    joined_path = "_".join(key.path)
    return f"{joined_path}_in".replace("-", "_")


def build_job_from_airflow_dag(
    airflow_instance: AirflowInstance,
    dag_id: str,
    mapped_assets: Sequence[Union[AssetSpec, AssetsDefinition]],
) -> tuple[Union[UnresolvedAssetJobDefinition, JobDefinition], Sequence[AssetsDefinition]]:
    """Builds a Dagster job from an Airflow dag."""
    dags = airflow_instance.list_dags()
    datasets = airflow_instance.get_datasets()
    # TODO: automatically hook up lineage
    print(len(datasets))
    dag = check.not_none(next((d for d in dags if d.dag_id == dag_id), None))
    tasks = airflow_instance.get_task_infos(dag_id=dag_id)
    all_task_ids = {task.task_id for task in tasks}
    datasets_mapping_to_tasks = {
        task_id: [
            dataset
            for dataset in datasets
            if dataset.is_produced_by_task(dag_id=dag_id, task_id=task_id)
        ]
        for task_id in all_task_ids
    }
    datasets_to_downstream_dags = {
        dataset.uri: [dag.dag_id for dag in dataset.consuming_dags] for dataset in datasets
    }
    print(f"datasets_to_downstream_dags: {datasets_to_downstream_dags}")
    datasets_to_producing_dags = {
        dataset.uri: [task.dag_id for task in dataset.producing_tasks] for dataset in datasets
    }
    print(f"datasets_to_producing_dags: {datasets_to_producing_dags}")
    dataset_dependencies = {}
    for dataset in datasets:
        # A dataset is dependent on all the datasets which are consumed by the dags which produce it.
        producing_dags = datasets_to_producing_dags.get(dataset.uri, [])
        dataset_dependencies[dataset.uri] = []
        for potential_upstream in datasets_to_downstream_dags.keys():
            downstream_dags = datasets_to_downstream_dags.get(potential_upstream, [])
            for downstream_dag_id in downstream_dags:
                print(f"downstream_dag_id: {downstream_dag_id}")
                print(f"producing_dags: {producing_dags}")
                if downstream_dag_id in producing_dags:
                    # Then dataset has a dependency on pot_dataset.
                    dataset_dependencies[dataset.uri].append(potential_upstream)
                    print("ENTERED")
    if dataset_dependencies:
        print(dataset_dependencies)

    dataset_assets = [
        make_dataset_spec(dataset, dataset_dependencies.get(dataset.uri, []))
        for task_id, dataset_list in datasets_mapping_to_tasks.items()
        for dataset in dataset_list
    ]
    mapped_assets = list(mapped_assets) + dataset_assets

    task_dep_structure = {}
    downstream_task_structure = {}
    for task in tasks:
        for downstream_task_id in task.downstream_task_ids:
            if downstream_task_id not in task_dep_structure:
                task_dep_structure[downstream_task_id] = []
            if task.task_id not in downstream_task_structure:
                downstream_task_structure[task.task_id] = []
            task_dep_structure[downstream_task_id].append(task.task_id)
            downstream_task_structure[task.task_id].append(downstream_task_id)

    def build_op(
        *,
        task_id: str,
        dep_tasks: list[str],
        outs: Mapping[str, dg.Out] = {"result": dg.Out(dagster_type=dg.Nothing)},
        additional_ins: Mapping[str, dg.In] = {},
    ) -> dg.OpDefinition:
        if "result" not in outs:
            print(task_id)
            print("changed outs")
            print(outs)
        all_ins = {
            **additional_ins,
            **{f"{dep_task}_in": dg.In(dagster_type=dg.Nothing) for dep_task in dep_tasks},
        }

        @dg.op(
            name=f"{dag_id}_{task_id}",
            tags={"airflow/task_id": task_id},
            ins=all_ins,
            out=outs,
        )
        def my_op(context: dg.OpExecutionContext):
            af_run_id = context.run_tags["airflow/run_id"]
            while task_state := airflow_instance.get_task_instance(
                dag_id=dag_id, task_id=task_id, run_id=af_run_id
            ):
                continuation_token = None
                while True:
                    try:
                        logs, continuation_token = airflow_instance.get_logs(
                            dag_id=dag_id,
                            task_id=task_id,
                            run_id=af_run_id,
                            token=continuation_token,
                        )
                    except Exception as e:
                        context.log.error(
                            f"Error fetching logs; likely bc airflow is asleep. Waiting.: {e}"
                        )
                        time.sleep(1)
                        continue

                    parsed_logs = parse_af_log_response(logs)
                    if len(parsed_logs) == 1 and parsed_logs[0][1] == "":
                        break
                    for log in parsed_logs:
                        context.log.info(log[1])
                time.sleep(1)
                if task_state.state in ["success", "failed"]:
                    break

        print("output defs")
        print([output_def.name for output_def in my_op.output_defs])
        return my_op

    node_list = []
    terminal_op_name = None
    root_op_name = None
    assets_mapped = False
    deps_mapped = False
    for task_id in all_task_ids:
        if not task_dep_structure.get(task_id) and not deps_mapped:
            deps_mapped = True

            additional_ins = {
                make_input_name_from_key(dep.asset_key): dg.In(dagster_type=dg.Nothing)
                for asset in mapped_assets
                for dep in cast(dg.AssetSpec, asset).deps
            }
            op_def = build_op(
                task_id=task_id,
                dep_tasks=task_dep_structure.get(task_id, []),
                additional_ins=additional_ins,
            )
            root_op_name = op_def.name
        elif not downstream_task_structure.get(task_id) and not assets_mapped:
            assets_mapped = True
            # Hijack the outputs on the terminal task to be the mapped assets.
            additional_outputs = {
                make_output_name_from_key(asset.key): dg.Out(dagster_type=dg.Nothing)
                for asset in mapped_assets
            }
            print("ADDITIONAL OUTPUTS")
            print(additional_outputs)
            op_def = build_op(
                task_id=task_id,
                dep_tasks=task_dep_structure.get(task_id, []),
                outs=additional_outputs,
            )
            terminal_op_name = op_def.name
        else:
            op_def = build_op(task_id=task_id, dep_tasks=task_dep_structure.get(task_id, []))

        node_list.append(op_def)

    if len(mapped_assets) > 0:
        output_mappings = [
            OutputMapping(
                graph_output_name=make_output_name_from_key(asset.key),
                mapped_node_name=check.not_none(terminal_op_name),
                mapped_node_output_name=make_output_name_from_key(asset.key),
            )
            for asset in mapped_assets
        ]
        input_mappings = [
            InputMapping(
                graph_input_name=make_input_name_from_key(dep.asset_key),
                mapped_node_name=check.not_none(root_op_name),
                mapped_node_input_name=make_input_name_from_key(dep.asset_key),
            )
            for asset in mapped_assets
            for dep in cast(dg.AssetSpec, asset).deps
        ]
        print("ENTERED_MAPPED_ASSETS")
        print(len(output_mappings))
        print(output_mappings)
        graph_def = dg.GraphDefinition(
            name=f"graph_{dag_id}",
            node_defs=node_list,
            dependencies={
                f"{dag_id}_{task_id}": {
                    f"{dep_task_id}_in": dg.DependencyDefinition(f"{dag_id}_{dep_task_id}")
                    for dep_task_id in dep_tasks
                }
                for task_id, dep_tasks in task_dep_structure.items()
            },
            output_mappings=output_mappings,
            input_mappings=input_mappings,
        )
        assets_def = dg.AssetsDefinition.from_graph(
            graph_def=graph_def,
            keys_by_output_name={
                make_output_name_from_key(asset.key): asset.key for asset in mapped_assets
            },
            keys_by_input_name={
                make_input_name_from_key(dep.asset_key): dep.asset_key
                for asset in mapped_assets
                for dep in cast(dg.AssetSpec, asset).deps
            },
            metadata_by_output_name={
                make_output_name_from_key(asset.key): asset.metadata for asset in mapped_assets
            },  # type: ignore # will always be asset spec right now
            tags_by_output_name={
                make_output_name_from_key(asset.key): {
                    f"{KIND_PREFIX}{kind}": "" for kind in asset.kinds
                }
                for asset in mapped_assets
            },  # type: ignore # will always be asset spec right now
        )
        print(assets_def.keys)
        my_af_job = dg.define_asset_job(
            name=dag_id,
            selection=[*assets_def.keys],
            tags={"airflow/dag_id": dag_id},
            executor_def=build_af_observation_executor(airflow_instance),
        )
        print(my_af_job.selection)
        return my_af_job, [assets_def]
    else:
        graph_def = dg.GraphDefinition(
            name=f"graph_{dag_id}",
            node_defs=node_list,
            dependencies={
                f"{dag_id}_{task_id}": {
                    f"{dep_task_id}_in": dg.DependencyDefinition(f"{dag_id}_{dep_task_id}")
                    for dep_task_id in dep_tasks
                }
                for task_id, dep_tasks in task_dep_structure.items()
            },
        )
        job_def = dg.JobDefinition(
            name=dag_id,
            graph_def=graph_def,
            tags={"airflow/dag_id": dag_id},
            executor_def=build_af_observation_executor(airflow_instance),
        )
        return job_def, []


@whitelist_for_serdes
@record
class AirflowJobPollingSensorCursor:
    """A cursor that stores the last effective timestamp and the last polled dag id."""

    start_date_gte: Optional[float] = None
    start_date_lte: Optional[float] = None
    dag_query_offset: Optional[int] = None


MAIN_LOOP_TIMEOUT_SECONDS = DEFAULT_SENSOR_GRPC_TIMEOUT - 20
DEFAULT_AIRFLOW_SENSOR_INTERVAL_SECONDS = 30
START_LOOKBACK_SECONDS = 60  # Lookback one minute in time for the initial setting of the cursor.


def build_observation_job_sensor(
    airflow_instance: AirflowInstance,
    jobs: list[dg.JobDefinition],
) -> dg.SensorDefinition:
    mapped_dags = {job.tags["airflow/dag_id"]: job for job in jobs}

    @dg.sensor(jobs=jobs, minimum_interval_seconds=1, default_status=dg.DefaultSensorStatus.RUNNING)
    def sensor_detects_af_runs(context: dg.SensorEvaluationContext):
        context.log.info(f"************Running sensor for {airflow_instance.name}***********")
        try:
            cursor = (
                deserialize_value(context.cursor, AirflowJobPollingSensorCursor)
                if context.cursor
                else AirflowJobPollingSensorCursor()
            )
        except Exception as e:
            context.log.info(f"Failed to interpret cursor. Starting from scratch. Error: {e}")
            cursor = AirflowJobPollingSensorCursor()
        current_date = get_current_datetime()
        current_dag_offset = cursor.dag_query_offset or 0
        start_date_gte = (
            cursor.start_date_gte
            or (current_date - timedelta(seconds=START_LOOKBACK_SECONDS)).timestamp()
        )
        start_date_lte = cursor.start_date_lte or current_date.timestamp()

        sensor_iter = run_requests_iter(
            context=context,
            start_date_gte=start_date_gte,
            start_date_lte=start_date_lte,
            offset=current_dag_offset,
            airflow_instance=airflow_instance,
            mapped_dags=mapped_dags,
        )
        latest_offset = current_dag_offset
        run_requests = []
        while get_current_datetime() - current_date < timedelta(seconds=MAIN_LOOP_TIMEOUT_SECONDS):
            batch_result = next(sensor_iter, None)
            if batch_result is None:
                context.log.info("Received no batch result. Breaking.")
                break
            run_requests.extend(batch_result.run_requests)
            latest_offset = batch_result.idx

        if batch_result is not None:
            new_cursor = AirflowJobPollingSensorCursor(
                start_date_gte=start_date_gte,
                start_date_lte=start_date_lte,
                dag_query_offset=latest_offset + 1,
            )
        else:
            # We have completed iteration for this range
            new_cursor = AirflowJobPollingSensorCursor(
                start_date_gte=start_date_lte,
                start_date_lte=None,
                dag_query_offset=0,
            )

        context.update_cursor(serialize_value(new_cursor))

        return dg.SensorResult(run_requests=run_requests)

    return sensor_detects_af_runs


@record
class BatchResult:
    idx: int
    run_requests: Sequence[RunRequest]


def run_requests_iter(
    context: dg.SensorEvaluationContext,
    start_date_gte: float,
    start_date_lte: float,
    offset: int,
    airflow_instance: AirflowInstance,
    mapped_dags: dict[str, dg.JobDefinition],
) -> Iterator[Optional[BatchResult]]:
    total_processed_runs = 0
    total_entries = 0
    while True:
        latest_offset = total_processed_runs + offset
        context.log.info(
            f"Fetching dag runs for {airflow_instance.name} with offset {latest_offset}..."
        )
        context.log.info(f"Dag ids: {list(mapped_dags.keys())}")
        runs, total_entries = airflow_instance.get_dag_runs_batch(
            dag_ids=list(mapped_dags.keys()),
            start_date_gte=datetime_from_timestamp(start_date_gte),
            start_date_lte=datetime_from_timestamp(start_date_lte),
            offset=latest_offset,
            # TODO: figure out what we actually want to do here, since we're probably gonna end up missing runs that complete
            # too quickly.
            states=["running"],
        )
        if len(runs) == 0:
            yield None
            context.log.info("Received no runs. Breaking.")
            break
        else:
            context.log.info("FOUND DAG RUNS")
        context.log.info(
            f"Processing {len(runs)}/{total_entries} dag runs for {airflow_instance.name}..."
        )
        for i, dag_run in enumerate(runs):
            yield BatchResult(
                idx=i + latest_offset,
                run_requests=[
                    RunRequest(
                        job_name=mapped_dags[dag_run.dag_id].name,
                        run_key=dag_run.run_id,
                        tags={"airflow/run_id": dag_run.run_id},
                    )
                ],
            )
        total_processed_runs += len(runs)
        context.log.info(
            f"Processed {total_processed_runs}/{total_entries} dag runs for {airflow_instance.name}."
        )
        if total_processed_runs == total_entries:
            yield None
            context.log.info("Processed all runs. Breaking.")
            break


def _handle_compute_log_setup_error(
    context: PlanExecutionContext, exc_info
) -> Iterator[DagsterEvent]:
    yield DagsterEvent.engine_event(
        plan_context=context,
        message="Exception while setting up compute log capture",
        event_specific_data=EngineEventData(error=serializable_error_info_from_exc_info(exc_info)),
    )


def _handle_compute_log_teardown_error(
    context: PlanExecutionContext, exc_info
) -> Iterator[DagsterEvent]:
    yield DagsterEvent.engine_event(
        plan_context=context,
        message="Exception while cleaning up compute log capture",
        event_specific_data=EngineEventData(error=serializable_error_info_from_exc_info(exc_info)),
    )


def build_airflow_execution_iterator(
    airflow_instance: AirflowInstance,
) -> Callable[..., Iterator[DagsterEvent]]:
    def _airflow_execution_iterator(
        job_context: PlanExecutionContext,
        execution_plan: ExecutionPlan,
        instance_concurrency_context: Optional[InstanceConcurrencyContext] = None,
    ) -> Iterator[dg.DagsterEvent]:
        check.inst_param(job_context, "pipeline_context", PlanExecutionContext)
        check.inst_param(execution_plan, "execution_plan", ExecutionPlan)
        compute_log_manager = job_context.instance.compute_log_manager
        step_keys = [step.key for step in execution_plan.get_steps_to_execute_in_topo_order()]
        with execution_plan.start(
            retry_mode=job_context.retry_mode,
            instance_concurrency_context=instance_concurrency_context,
        ) as active_execution:
            # TODO: trigger airflow run if there's none associated yet.
            with ExitStack() as capture_stack:
                # begin capturing logs for the whole process
                file_key = create_compute_log_file_key()
                log_key = compute_log_manager.build_log_key_for_run(job_context.run_id, file_key)
                try:
                    log_context = capture_stack.enter_context(
                        compute_log_manager.capture_logs(log_key)
                    )
                    yield DagsterEvent.capture_logs(job_context, step_keys, log_key, log_context)
                except Exception:
                    yield from _handle_compute_log_setup_error(job_context, sys.exc_info())

                # It would be good to implement a reference tracking algorithm here to
                # garbage collect results that are no longer needed by any steps
                # https://github.com/dagster-io/dagster/issues/811
                while not active_execution.is_complete:
                    next_executable_steps = active_execution.get_steps_to_execute()
                    if not next_executable_steps:
                        active_execution.sleep_til_ready()
                        continue
                    yield from active_execution.concurrency_event_iterator(job_context)
                    executable_step_dict = {step.key: step for step in next_executable_steps}
                    while executable_step_dict:
                        task_ids_to_query = {
                            step.tags["airflow/task_id"]: step
                            for step in executable_step_dict.values()
                        }
                        task_states = airflow_instance.get_task_instance_batch(
                            dag_id=job_context.run_tags["airflow/dag_id"],
                            task_ids=list(task_ids_to_query.keys()),
                            run_id=job_context.run_tags["airflow/run_id"],
                            states=["running", "success", "failed"],
                        )
                        task_state_per_task_id = {
                            task_state.task_id: task_state for task_state in task_states
                        }
                        steps_to_run = [
                            task_ids_to_query[task_id]
                            for task_id in task_ids_to_query
                            if task_id in task_state_per_task_id
                        ]
                        for step in steps_to_run:
                            del executable_step_dict[step.key]

                            step_context = cast(
                                StepExecutionContext,
                                job_context.for_step(step, active_execution.get_known_state()),
                            )
                            step_event_list = []

                            missing_resources = [
                                resource_key
                                for resource_key in step_context.required_resource_keys
                                if not hasattr(step_context.resources, resource_key)
                            ]
                            check.invariant(
                                len(missing_resources) == 0,
                                (
                                    f"Expected step context for solid {step_context.op.name} to have all required"
                                    f" resources, but missing {missing_resources}."
                                ),
                            )

                            # we have already set up the log capture at the process level, just handle the step events
                            for step_event in check.generator(
                                dagster_event_sequence_for_step(step_context)
                            ):
                                dagster_event = check.inst(step_event, DagsterEvent)
                                step_event_list.append(dagster_event)
                                yield dagster_event
                                active_execution.handle_event(dagster_event)

                            active_execution.verify_complete(job_context, step.key)

                            # process skips from failures or uncovered inputs
                            for event in active_execution.plan_events_iterator(job_context):
                                step_event_list.append(event)
                                yield event

                            # Hooks aren't gonna be used here
                            # yield from _trigger_hook(step_context, step_event_list)

                try:
                    capture_stack.close()
                except Exception:
                    yield from _handle_compute_log_teardown_error(job_context, sys.exc_info())

    return _airflow_execution_iterator


def dagster_event_sequence_for_step(
    step_context: StepExecutionContext, force_local_execution: bool = False
) -> Iterator[DagsterEvent]:
    """Yield a sequence of dagster events for the given step with the step context.

    This function also processes errors. It handles a few error cases:

        (1) User code requests to be retried:
            A RetryRequested has been raised. We will either put the step in to
            up_for_retry state or a failure state depending on the number of previous attempts
            and the max_retries on the received RetryRequested.

        (2) User code fails successfully:
            The user-space code has raised a Failure which may have
            explicit metadata attached.

        (3) User code fails unexpectedly:
            The user-space code has raised an Exception. It has been
            wrapped in an exception derived from DagsterUserCodeException. In that
            case the original user exc_info is stashed on the exception
            as the original_exc_info property.

        (4) Execution interrupted:
            The run was interrupted in the middle of execution (typically by a
            termination request).

        (5) Dagster framework error:
            The framework raised a DagsterError that indicates a usage error
            or some other error not communicated by a user-thrown exception. For example,
            if the user yields an object out of a compute function that is not a
            proper event (not an Output, ExpectationResult, etc).

        (6) All other errors:
            An unexpected error occurred. Either there has been an internal error in the framework
            OR we have forgotten to put a user code error boundary around invoked user-space code.


    The "raised_dagster_errors" context manager can be used to force these errors to be
    re-raised and surfaced to the user. This is mostly to get sensible errors in test and
    ad-hoc contexts, rather than forcing the user to wade through the
    JobExecutionResult API in order to find the step that failed.

    For tools, however, this option should be false, and a sensible error message
    signaled to the user within that tool.

    When we launch a step that has a step launcher, we use this function on both the host process
    and the remote process. When we run the step in the remote process, to prevent an infinite loop
    of launching steps that then launch steps, and so on, the remote process will run this with
    the force_local_execution argument set to True.
    """
    check.inst_param(step_context, "step_context", StepExecutionContext)

    try:
        if step_context.step_launcher and not force_local_execution:
            # info all on step_context - should deprecate second arg
            step_events = step_context.step_launcher.launch_step(step_context)
        else:
            step_events = core_dagster_event_sequence_for_step(step_context)

        yield from check.generator(step_events)

    # case (1) in top comment
    except RetryRequested as retry_request:
        retry_err_info = serializable_error_info_from_exc_info(sys.exc_info())

        if step_context.retry_mode.disabled:
            fail_err = SerializableErrorInfo(
                message="RetryRequested but retries are disabled",
                stack=retry_err_info.stack,
                cls_name=retry_err_info.cls_name,
                cause=retry_err_info.cause,
            )
            step_context.capture_step_exception(retry_request)
            yield DagsterEvent.step_failure_event(
                step_context=step_context,
                step_failure_data=StepFailureData(
                    error=fail_err,
                    user_failure_data=_user_failure_data_for_exc(retry_request.__cause__),
                ),
            )
        else:  # retries.enabled or retries.deferred
            prev_attempts = step_context.previous_attempt_count
            if prev_attempts >= retry_request.max_retries:
                fail_err = SerializableErrorInfo(
                    message=f"Exceeded max_retries of {retry_request.max_retries}\n",
                    stack=retry_err_info.stack,
                    cls_name=retry_err_info.cls_name,
                    cause=retry_err_info.cause,
                )
                step_context.capture_step_exception(retry_request)
                yield DagsterEvent.step_failure_event(
                    step_context=step_context,
                    step_failure_data=StepFailureData(
                        error=fail_err,
                        user_failure_data=_user_failure_data_for_exc(retry_request.__cause__),
                        # set the flag to omit the outer stack if we have a cause to show
                        error_source=ErrorSource.USER_CODE_ERROR if fail_err.cause else None,
                    ),
                )
                if step_context.raise_on_error:
                    raise DagsterMaxRetriesExceededError.from_error_info(fail_err)
            else:
                yield DagsterEvent.step_retry_event(
                    step_context,
                    StepRetryData(
                        error=retry_err_info,
                        seconds_to_wait=retry_request.seconds_to_wait,
                    ),
                )

    # case (2) in top comment
    except Failure as failure:
        step_context.capture_step_exception(failure)
        yield step_failure_event_from_exc_info(
            step_context,
            sys.exc_info(),
            _user_failure_data_for_exc(failure),
        )
        if step_context.raise_on_error:
            raise failure

    # case (3) in top comment
    except DagsterUserCodeExecutionError as dagster_user_error:
        step_context.capture_step_exception(dagster_user_error.user_exception)
        yield step_failure_event_from_exc_info(
            step_context,
            sys.exc_info(),
            error_source=ErrorSource.USER_CODE_ERROR,
        )

        if step_context.raise_on_error:
            raise dagster_user_error.user_exception

    # case (4) in top comment
    except (KeyboardInterrupt, DagsterExecutionInterruptedError) as interrupt_error:
        step_context.capture_step_exception(interrupt_error)
        yield step_failure_event_from_exc_info(
            step_context,
            sys.exc_info(),
            error_source=ErrorSource.INTERRUPT,
        )
        raise interrupt_error

    # cases (5) and (6) in top comment
    except BaseException as error:
        step_context.capture_step_exception(error)
        yield step_failure_event_from_exc_info(
            step_context,
            sys.exc_info(),
            error_source=(
                ErrorSource.FRAMEWORK_ERROR
                if isinstance(error, DagsterError)
                else ErrorSource.UNEXPECTED_ERROR
            ),
        )

        if step_context.raise_on_error:
            raise error


def _user_failure_data_for_exc(exc: Optional[BaseException]) -> Optional[UserFailureData]:
    if isinstance(exc, Failure):
        return UserFailureData(
            label="intentional-failure",
            description=exc.description,
            metadata=exc.metadata,
        )

    return None


def build_af_observation_executor(airflow_instance: AirflowInstance):
    # A bunch of cargo culting from in process executor.
    class AirflowObservationExecutor(dg.Executor):
        def execute(
            self, plan_context: PlanOrchestrationContext, execution_plan: ExecutionPlan
        ) -> Iterator[DagsterEvent]:
            check.inst_param(plan_context, "plan_context", PlanOrchestrationContext)
            check.inst_param(execution_plan, "execution_plan", ExecutionPlan)

            step_keys_to_execute = execution_plan.step_keys_to_execute

            yield DagsterEvent.engine_event(
                plan_context,
                f"Executing steps in process (pid: {os.getpid()})",
                event_specific_data=EngineEventData.in_process(os.getpid(), step_keys_to_execute),
            )

            with time_execution_scope() as timer_result:
                yield from iter(
                    ExecuteRunWithPlanIterable(
                        execution_plan=plan_context.execution_plan,
                        iterator=build_airflow_execution_iterator(airflow_instance),
                        execution_context_manager=PlanExecutionContextManager(
                            job=plan_context.job,
                            retry_mode=plan_context.retry_mode,
                            execution_plan=plan_context.execution_plan,
                            run_config=plan_context.run_config,
                            dagster_run=plan_context.dagster_run,
                            instance=plan_context.instance,
                            raise_on_error=plan_context.raise_on_error,
                            output_capture=plan_context.output_capture,
                        ),
                    )
                )

            yield DagsterEvent.engine_event(
                plan_context,
                f"Finished steps in process (pid: {os.getpid()}) in {format_duration(timer_result.millis)}",
                event_specific_data=EngineEventData.in_process(os.getpid(), step_keys_to_execute),
            )

        # Not sure what we would want to do in a real implementation
        @property
        def retries(self):
            return RetryMode.DISABLED

    @dg.executor(
        name="airflow_observation_executor",
    )
    def airflow_observation_executor(context):
        return AirflowObservationExecutor()

    return airflow_observation_executor
