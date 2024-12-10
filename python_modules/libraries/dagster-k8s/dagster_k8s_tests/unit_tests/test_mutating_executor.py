from typing import List
from unittest import mock

from dagster import (
    DagsterInstance,
    DagsterRun,
    Executor,
    InitExecutorContext,
    InMemoryIOManager,
    IOManagerDefinition,
    JobDefinition,
    OpExecutionContext,
    StepExecutionContext,
    io_manager,
    job,
    op,
    reconstructable,
)
from dagster._config import process_config, resolve_to_config_type
from dagster._core.definitions import ReconstructableJob
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.context.system import PlanData, PlanOrchestrationContext
from dagster._core.execution.context_creation_job import create_context_free_log_manager
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.step_delegating import StepHandlerContext
from dagster._grpc.types import ExecuteStepArgs
from dagster_k8s.container_context import K8sContainerContext
from dagster_k8s.op_mutating_executor import (
    _K8S_OP_EXECUTOR_CONFIG_SCHEMA,
    K8sMutatingStepHandler,
    K8sOpMutatingOutput,
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
MOCK_K8s_OUTPUT = K8sOpMutatingOutput({"container_config": MOCK_RUNTIME_RESOURCE_CONF})


@job
def simple_producer_consumer():
    @op
    def producer() -> K8sOpMutatingOutput:
        return MOCK_K8s_OUTPUT

    @op
    def sink(context: OpExecutionContext, producer: K8sOpMutatingOutput):
        context.log.info(f"received the following input: {producer}")

    sink(producer())


def _fetch_step_handler_context(
    job_def: ReconstructableJob,
    dagster_run: DagsterRun,
    instance: DagsterInstance,
    executor: Executor,
    steps: List[str],
):
    execution_plan = create_execution_plan(job_def)
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
        steps=execution_plan.steps,
        execute_step_args=execute_step_args,
    )


def _fetch_mutating_executor(
    instance: DagsterInstance, job_def: JobDefinition, executor_config=None
):
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


def _make_shared_mem_io_manager(inmem_io_manager: InMemoryIOManager) -> IOManagerDefinition:
    @io_manager
    def shared_mem_io_manager(_) -> InMemoryIOManager:
        return inmem_io_manager

    return shared_mem_io_manager


def test_mutating_step_handler_runtime_override(
    k8s_instance: DagsterInstance, kubeconfig_file: str
):
    """Using the `simple_producer_consumer` job, ensure that a simple output can be detected, eagerly loaded, and consumed as container context."""
    mock_k8s_client_batch_api = mock.MagicMock()
    run_id = "de07af8f-d5f4-4a43-b545-132c3310999d"
    shared_mem_io_manager = InMemoryIOManager()
    io_manager_def = _make_shared_mem_io_manager(shared_mem_io_manager)
    result = simple_producer_consumer.execute_in_process(
        instance=k8s_instance, run_id=run_id, resources={"io_manager": io_manager_def}
    )
    assert result.success
    recon_job = reconstructable(simple_producer_consumer)
    executor = _fetch_mutating_executor(k8s_instance, recon_job)
    step_handler_ctx = _fetch_step_handler_context(
        recon_job, result.dagster_run, k8s_instance, executor, ["sink"]
    )
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
    with mock.patch.object(
        StepExecutionContext, "get_io_manager", mock.MagicMock(return_value=shared_mem_io_manager)
    ):
        runtime_mutated_context = handler._get_container_context(step_handler_ctx)  # noqa: SLF001
    assert (
        runtime_mutated_context.run_k8s_config.container_config.get("resources")
        == MOCK_RUNTIME_RESOURCE_CONF["resources"]
    )
    # check cache state
    assert len(handler.step_input_cache) == 1
    # no need to stub execution context again as the step_input_cache should now hit. If not below will fail.
    list(handler.terminate_step(step_handler_ctx))
    # ensure clean events are handled
    assert not handler.step_input_cache


def test_mutating_step_handler_no_runtime_override(k8s_instance: DagsterInstance, kubeconfig_file):
    """Ensure that when disabled, we fallback to the behavior of the  K8sStepHandler."""
    mock_k8s_client_batch_api = mock.MagicMock()
    result = simple_producer_consumer.execute_in_process(instance=k8s_instance)
    assert result.success
    recon_job = reconstructable(simple_producer_consumer)
    executor = _fetch_mutating_executor(k8s_instance, recon_job)
    step_handler_ctx = _fetch_step_handler_context(
        recon_job, result.dagster_run, k8s_instance, executor, ["sink"]
    )
    initial_resources = {
        "requests": {"cpu": "128m", "memory": "64Mi"},
        "limits": {"cpu": "500m", "memory": "1000Mi"},
    }
    handler = K8sMutatingStepHandler(
        image="bizbuz",
        container_context=K8sContainerContext(
            namespace="foo",
            resources=initial_resources,
        ),
        load_incluster_config=False,
        kubeconfig_file=kubeconfig_file,
        k8s_client_batch_api=mock_k8s_client_batch_api,
        op_mutation_enabled=False,
    )
    runtime_mutated_context = handler._get_container_context(step_handler_ctx)  # noqa: SLF001
    assert (
        runtime_mutated_context.run_k8s_config.container_config.get("resources")
        == initial_resources
    )
    assert not handler.step_input_cache
