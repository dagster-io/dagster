from dataclasses import dataclass
from typing import List, Sequence, cast
from unittest import mock

import pytest
from dagster import (
    DagsterInstance,
    DagsterRun,
    DynamicOut,
    DynamicOutput,
    Executor,
    In,
    InitExecutorContext,
    JsonMetadataValue,
    OpExecutionContext,
    Out,
    Output,
    job,
    op,
    reconstructable,
)
from dagster._config import process_config, resolve_to_config_type
from dagster._core.definitions import ReconstructableJob
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.context.system import PlanData, PlanOrchestrationContext
from dagster._core.execution.context_creation_job import create_context_free_log_manager
from dagster._core.execution.plan.state import KnownExecutionState
from dagster._core.execution.plan.step import ExecutionStep
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.step_delegating import StepHandlerContext
from dagster._core.storage.event_log import SqlEventLogStorage
from dagster._grpc.types import ExecuteStepArgs
from dagster_k8s.container_context import K8sContainerContext
from dagster_k8s.job import USER_DEFINED_K8S_CONFIG_KEY, UserDefinedDagsterK8sConfig
from dagster_k8s.op_mutating_executor import (
    _K8S_OP_EXECUTOR_CONFIG_SCHEMA,
    USER_DEFINED_INPUT_K8S_OP_MUTATION_KEY,
    K8sMutatingStepHandler,
    K8sOpMutatingWrapper,
    get_output_records_for_run_step,
    k8s_op_mutating_executor,
)

from dagster_k8s_tests.unit_tests.test_executor import k8s_instance

_ = k8s_instance

MOCK_RUNTIME_RESOURCE_CONF = {
    "resources": {
        "requests": {"cpu": "3500m", "memory": "4Gi"},
        "limits": {"cpu": "4200m", "memory": "5Gi"},
    }
}


@job
def simple_producer_consumer_job():
    @op(out=Out(K8sOpMutatingWrapper))
    def producer():
        return Output(
            K8sOpMutatingWrapper[int](1),
            metadata={
                USER_DEFINED_K8S_CONFIG_KEY: {"container_config": MOCK_RUNTIME_RESOURCE_CONF}
            },
        )

    @op
    def sink(context: OpExecutionContext, producer: K8sOpMutatingWrapper) -> KnownExecutionState:
        _ = producer
        return context.get_step_execution_context().get_known_state()

    sink(producer())


@job
def dynamic_producer_consumer_job():
    @op(out=DynamicOut(K8sOpMutatingWrapper))
    def dyn_producer():
        for i in [3, 4]:
            k8s_out = K8sOpMutatingWrapper[int](1)
            yield DynamicOutput(
                k8s_out,
                str(i),
                metadata={
                    USER_DEFINED_K8S_CONFIG_KEY: {
                        "container_config": {
                            "resources": {
                                "requests": {"cpu": f"{i}234m", "memory": f"{i}Gi"},
                                "limits": {"cpu": f"{i}765m", "memory": f"{i}Gi"},
                            }
                        }
                    }
                },
            )

    @op
    def dyn_sink(
        context: OpExecutionContext, producer: K8sOpMutatingWrapper
    ) -> KnownExecutionState:
        context.log.info(f"received the following input: {producer}")
        # hacky way for to get known context -> InMemIOManager -> StepOrchestrationContext
        # for step handler testing
        return context.get_step_execution_context().get_known_state()

    dyn_producer().map(dyn_sink).collect()


@job
def input_metadata_simple_job():
    @op
    def simple_op_out_with_metadata() -> Output[int]:
        return Output(
            1,
            metadata={
                USER_DEFINED_K8S_CONFIG_KEY: {"container_config": MOCK_RUNTIME_RESOURCE_CONF}
            },
        )

    @op(
        ins={
            "simple_op_out_with_metadata": In(
                int, metadata={USER_DEFINED_INPUT_K8S_OP_MUTATION_KEY: True}
            )
        }
    )
    def simple_metadata_consumer(context: OpExecutionContext, simple_op_out_with_metadata: int):
        context.log.info(f"received the following input: {simple_op_out_with_metadata}")

    simple_metadata_consumer(simple_op_out_with_metadata())


@job
def multi_input_simple_job():
    @op
    def simple_out_one() -> Output[K8sOpMutatingWrapper]:
        return Output(
            K8sOpMutatingWrapper(1),
            metadata={
                USER_DEFINED_K8S_CONFIG_KEY: {
                    "container_config": {
                        "resources": {
                            "requests": {"cpu": "1234m", "memory": "1Gi"},
                            "limits": {"cpu": "1765m", "memory": "1Gi"},
                        }
                    }
                }
            },
        )

    @op
    def simple_mem_override() -> Output[K8sOpMutatingWrapper]:
        return Output(
            K8sOpMutatingWrapper(1),
            metadata={
                USER_DEFINED_K8S_CONFIG_KEY: {
                    "container_config": {
                        "resources": {
                            "requests": {"memory": "2Gi"},
                            "limits": {"memory": "2Gi"},
                        }
                    }
                }
            },
        )

    @op
    def dual_sink(
        simple_out_one: K8sOpMutatingWrapper, simple_mem_override: K8sOpMutatingWrapper
    ): ...

    dual_sink(simple_out_one(), simple_mem_override())


@dataclass
class MockStepOrchestrationContext:
    run_id: str
    log: SqlEventLogStorage


def _fetch_step_handler_context(
    job_def: ReconstructableJob,
    dagster_run: DagsterRun,
    instance: DagsterInstance,
    executor: Executor,
    steps: List[str],
    known_state=None,
):
    execution_plan = create_execution_plan(
        job_def, known_state=known_state, instance_ref=instance.get_ref()
    )
    log_manager = create_context_free_log_manager(instance, dagster_run)

    plan_context = PlanOrchestrationContext(
        plan_data=PlanData(
            job=job_def,
            dagster_run=dagster_run,
            instance=instance,
            execution_plan=execution_plan,
            raise_on_error=True,
            retry_mode=RetryMode.DISABLED,
        ),
        log_manager=log_manager,
        executor=executor,
        output_capture=None,
    )

    execute_step_args = ExecuteStepArgs(
        job_def.get_python_origin(),
        dagster_run.run_id,
        steps,
        print_serialized_events=False,
    )

    return StepHandlerContext(
        instance=instance,
        plan_context=plan_context,
        steps=cast(Sequence[ExecutionStep], execution_plan.steps),
        execute_step_args=execute_step_args,
    )


def _fetch_mutating_executor(instance, job_def, executor_config=None):
    process_result = process_config(
        resolve_to_config_type(_K8S_OP_EXECUTOR_CONFIG_SCHEMA),
        executor_config or {},
    )
    assert process_result.success, str(process_result.errors)

    return k8s_op_mutating_executor.executor_creation_fn(
        InitExecutorContext(
            job=job_def,
            executor_def=k8s_op_mutating_executor,
            executor_config=process_result.value,
            instance=instance,
        )
    )


@pytest.fixture
def mutating_step_handler(kubeconfig_file: str) -> K8sMutatingStepHandler:
    mock_k8s_client_batch_api = mock.MagicMock()
    handler = K8sMutatingStepHandler(
        image="bizbuz",
        container_context=K8sContainerContext(
            namespace="foo",
            resources={
                "requests": {"cpu": "128m", "memory": "64Mi"},
                "limits": {"cpu": "500m", "memory": "1000Mi"},
            },
        ),
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
        op_mutation_enabled=True,
    )
    # stub api client
    handler._api_client = mock.MagicMock()  # noqa: SLF001
    return handler


def test_get_step_output_records_simple(k8s_instance: DagsterInstance):
    run_id = "de07af8f-d5f4-4a43-b545-132c3310999d"
    result = simple_producer_consumer_job.execute_in_process(instance=k8s_instance, run_id=run_id)
    assert result.success
    event_conn = get_output_records_for_run_step(
        cast(SqlEventLogStorage, k8s_instance.event_log_storage),
        run_id,
        "producer",
    )
    assert not event_conn.has_more
    event_records = event_conn.records
    assert len(event_records) == 1
    event_entry = event_records[0].event_log_entry
    output_data = event_entry.get_dagster_event().step_output_data
    metadata = cast(JsonMetadataValue, output_data.metadata[USER_DEFINED_K8S_CONFIG_KEY])
    UserDefinedDagsterK8sConfig.from_dict(metadata.data)


def test_get_step_output_records_paginate(k8s_instance: DagsterInstance):
    run_id = "de07af8f-d5f4-4a43-b545-132c3310999d"
    result = dynamic_producer_consumer_job.execute_in_process(instance=k8s_instance, run_id=run_id)
    assert result.success
    upstream_step = "dyn_producer"
    event_conn = get_output_records_for_run_step(
        cast(SqlEventLogStorage, k8s_instance.event_log_storage),
        run_id,
        upstream_step,
        limit=1,
    )
    assert event_conn.has_more
    event_records = event_conn.records
    assert len(event_records) == 1
    event_entry = event_records[0].event_log_entry
    output_data = event_entry.get_dagster_event().step_output_data
    metadata = cast(JsonMetadataValue, output_data.metadata[USER_DEFINED_K8S_CONFIG_KEY])
    UserDefinedDagsterK8sConfig.from_dict(metadata.data)
    event_conn = get_output_records_for_run_step(
        cast(SqlEventLogStorage, k8s_instance.event_log_storage),
        run_id,
        upstream_step,
        cursor=event_conn.cursor,
    )
    assert not event_conn.has_more
    event_records = event_conn.records
    assert len(event_records) == 1
    event_entry = event_records[0].event_log_entry
    output_data = event_entry.get_dagster_event().step_output_data
    metadata = cast(JsonMetadataValue, output_data.metadata[USER_DEFINED_K8S_CONFIG_KEY])
    UserDefinedDagsterK8sConfig.from_dict(metadata.data)


def test_mutating_step_handler_runtime_override(
    k8s_instance: DagsterInstance, mutating_step_handler: K8sMutatingStepHandler
):
    """Using the `simple_producer_consumer` job, ensure that a simple output can be detected, eagerly loaded, and consumed as container context.

    The detection of mutation is via the custom defined K8sOpMutatingWrapper type.
    """
    run_id = "de07af8f-d5f4-4a43-b545-132c3310999d"
    result = simple_producer_consumer_job.execute_in_process(instance=k8s_instance, run_id=run_id)
    assert result.success
    recon_job = reconstructable(simple_producer_consumer_job)
    executor = _fetch_mutating_executor(k8s_instance, recon_job)
    step_handler_ctx = _fetch_step_handler_context(
        recon_job, result.dagster_run, k8s_instance, executor, ["sink"]
    )
    runtime_mutated_context = mutating_step_handler._get_container_context(step_handler_ctx)  # noqa: SLF001
    assert (
        runtime_mutated_context.run_k8s_config.container_config.get("resources")
        == MOCK_RUNTIME_RESOURCE_CONF["resources"]
    )
    # check cache state
    assert len(mutating_step_handler.container_ctx_cache) == 1
    # no need to stub execution context again as the step_input_cache should now hit. If not below will fail.
    list(mutating_step_handler.terminate_step(step_handler_ctx))
    # ensure clean events are handled
    assert not mutating_step_handler.container_ctx_cache


def test_mutating_step_handler_cache_hit(
    k8s_instance: DagsterInstance, mutating_step_handler: K8sMutatingStepHandler
):
    run_id = "de07af8f-d5f4-4a43-b545-132c3310999d"
    result = simple_producer_consumer_job.execute_in_process(instance=k8s_instance, run_id=run_id)
    assert result.success
    recon_job = reconstructable(simple_producer_consumer_job)
    executor = _fetch_mutating_executor(k8s_instance, recon_job)
    step_handler_ctx = _fetch_step_handler_context(
        recon_job, result.dagster_run, k8s_instance, executor, ["sink"]
    )
    runtime_mutated_context = mutating_step_handler._get_container_context(step_handler_ctx)  # noqa: SLF001
    assert (
        runtime_mutated_context.run_k8s_config.container_config.get("resources")
        == MOCK_RUNTIME_RESOURCE_CONF["resources"]
    )
    mutating_step_handler._merge_input_configs = mock.MagicMock()  # noqa: SLF001
    runtime_mutated_context = mutating_step_handler._get_container_context(step_handler_ctx)  # noqa: SLF001
    mutating_step_handler._merge_input_configs.assert_not_called()  # noqa: SLF001


def test_mutating_step_handler_dual_input(
    k8s_instance: DagsterInstance, mutating_step_handler: K8sMutatingStepHandler
):
    run_id = "de07af8f-d5f4-4a43-b545-132c3310999d"
    result = multi_input_simple_job.execute_in_process(instance=k8s_instance, run_id=run_id)
    assert result.success
    recon_job = reconstructable(multi_input_simple_job)
    executor = _fetch_mutating_executor(k8s_instance, recon_job)
    step_handler_ctx = _fetch_step_handler_context(
        recon_job, result.dagster_run, k8s_instance, executor, ["dual_sink"]
    )
    runtime_mutated_context = mutating_step_handler._get_container_context(step_handler_ctx)  # noqa: SLF001
    assert runtime_mutated_context.run_k8s_config.container_config.get("resources") == {
        "requests": {"cpu": "1234m", "memory": "2Gi"},
        "limits": {"cpu": "1765m", "memory": "2Gi"},
    }
    assert len(mutating_step_handler.container_ctx_cache) == 1
    list(mutating_step_handler.terminate_step(step_handler_ctx))
    assert not mutating_step_handler.container_ctx_cache


def test_mutating_step_handler_input_metadata_trigger(
    k8s_instance: DagsterInstance, mutating_step_handler: K8sMutatingStepHandler
):
    """Using the `input_metadata_simple_job` job, ensure that a simple output can be detected, eagerly loaded, and consumed as container context.

    The detection of mutation is via input metadata key by USER_DEFINED_INPUT_K8S_OP_MUTATION_KEY.
    """
    run_id = "de07af8f-d5f4-4a43-b545-132c3310999d"
    result = input_metadata_simple_job.execute_in_process(instance=k8s_instance, run_id=run_id)
    assert result.success
    recon_job = reconstructable(input_metadata_simple_job)
    executor = _fetch_mutating_executor(k8s_instance, recon_job)
    step_handler_ctx = _fetch_step_handler_context(
        recon_job, result.dagster_run, k8s_instance, executor, ["simple_metadata_consumer"]
    )
    runtime_mutated_context = mutating_step_handler._get_container_context(step_handler_ctx)  # noqa: SLF001
    assert (
        runtime_mutated_context.run_k8s_config.container_config.get("resources")
        == MOCK_RUNTIME_RESOURCE_CONF["resources"]
    )
    # check cache state
    assert len(mutating_step_handler.container_ctx_cache) == 1
    # no need to stub execution context again as the step_input_cache should now hit. If not below will fail.
    list(mutating_step_handler.terminate_step(step_handler_ctx))
    # ensure clean events are handled
    assert not mutating_step_handler.container_ctx_cache


def test_mutating_step_handler_dynamic_runtime_override(
    k8s_instance: DagsterInstance, mutating_step_handler: K8sMutatingStepHandler
):
    """Using the `dynamic_producer_consumer` job, validate container context changes with respect to runtime dynamic outputs.

    We do this by executing the job in memory as normal, we then construct a StepOrchestration context by pulling
    various state from the in memory job execution and reconstructing the orchestration context by hand.
    The constructed orchestration context should be representative of what the step orchestration context and known state
    would be when the actual job is ran.
    """
    run_id = "de07af8f-d5f4-4a43-b545-132c3310999d"
    result = dynamic_producer_consumer_job.execute_in_process(
        instance=k8s_instance,
        run_id=run_id,
    )
    assert result.success
    # for each mapping output, check the container context is propagated properly
    for i in [3, 4]:
        dyn_known_state = result.output_for_node("dyn_sink")[str(i)]
        recon_job = reconstructable(dynamic_producer_consumer_job)
        executor = _fetch_mutating_executor(k8s_instance, recon_job)
        step_handler_ctx = _fetch_step_handler_context(
            recon_job,
            result.dagster_run,
            k8s_instance,
            executor,
            [f"dyn_sink[{i}]"],
            dyn_known_state,
        )
        runtime_mutated_context = mutating_step_handler._get_container_context(step_handler_ctx)  # noqa: SLF001
        assert runtime_mutated_context.run_k8s_config.container_config.get("resources") == {
            "requests": {"cpu": f"{i}234m", "memory": f"{i}Gi"},
            "limits": {"cpu": f"{i}765m", "memory": f"{i}Gi"},
        }
        # check cache state
        assert len(mutating_step_handler.container_ctx_cache) == 1
        # no need to stub execution context again as the step_input_cache should now hit. If not below will fail.
        list(mutating_step_handler.terminate_step(step_handler_ctx))
        # ensure clean events are handled
        assert not mutating_step_handler.container_ctx_cache


def test_mutating_step_handler_no_runtime_override(
    k8s_instance: DagsterInstance, mutating_step_handler: K8sMutatingStepHandler
):
    """Ensure that when disabled, we fallback to the behavior of the K8sStepHandler."""
    mutating_step_handler.op_mutation_enabled = False
    result = simple_producer_consumer_job.execute_in_process(instance=k8s_instance)
    assert result.success
    recon_job = reconstructable(simple_producer_consumer_job)
    executor = _fetch_mutating_executor(k8s_instance, recon_job)
    step_handler_ctx = _fetch_step_handler_context(
        recon_job, result.dagster_run, k8s_instance, executor, ["sink"]
    )
    initial_resources = {
        "requests": {"cpu": "128m", "memory": "64Mi"},
        "limits": {"cpu": "500m", "memory": "1000Mi"},
    }
    runtime_mutated_context = mutating_step_handler._get_container_context(step_handler_ctx)  # noqa: SLF001
    assert (
        runtime_mutated_context.run_k8s_config.container_config.get("resources")
        == initial_resources
    )
    assert not mutating_step_handler.container_ctx_cache
    list(mutating_step_handler.terminate_step(step_handler_ctx))
