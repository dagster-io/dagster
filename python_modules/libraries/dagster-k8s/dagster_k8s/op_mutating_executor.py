from typing import Any, Mapping, NamedTuple, Optional, TypeVar, cast

from dagster import (
    Field,
    IOManager,
    StepRunRef,
    TypeCheck,
    _check as check,
    executor,
    usable_as_dagster_type,
)
from dagster._core.definitions.executor_definition import multiple_process_executor_requirements
from dagster._core.execution.context.system import StepOrchestrationContext
from dagster._core.execution.plan.external_step import step_run_ref_to_step_context
from dagster._core.execution.plan.inputs import (
    FromPendingDynamicStepOutput,
    FromStepOutput,
    StepInput,
)
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.base import Executor
from dagster._core.executor.init import InitExecutorContext
from dagster._core.executor.step_delegating import StepDelegatingExecutor, StepHandlerContext
from dagster._core.storage.input_manager import InputManager
from dagster._utils.merger import merge_dicts

from dagster_k8s.container_context import K8sContainerContext
from dagster_k8s.executor import _K8S_EXECUTOR_CONFIG_SCHEMA, K8sStepHandler
from dagster_k8s.job import UserDefinedDagsterK8sConfig
from dagster_k8s.launcher import K8sRunLauncher

_K8S_OP_EXECUTOR_CONFIG_SCHEMA = merge_dicts(
    _K8S_EXECUTOR_CONFIG_SCHEMA,
    {
        "op_mutation_enabled": Field(
            bool,
            default_value=False,
            description="enabled op configuration based on output of prior op",
        )
    },
)

T = TypeVar("T")


@usable_as_dagster_type
class K8sOpMutatingOutput:
    k8s_config: UserDefinedDagsterK8sConfig
    value: Any

    def __init__(
        self, k8s_config: UserDefinedDagsterK8sConfig | Mapping[str, Any], value: Any = None
    ):
        if isinstance(k8s_config, dict):
            check.mapping_param(k8s_config, "k8s_config", str)
            k8s_config = UserDefinedDagsterK8sConfig.from_dict(k8s_config)
        else:
            check.inst_param(k8s_config, "k8s_config", UserDefinedDagsterK8sConfig)
        self.k8s_config = k8s_config
        self.value = value

    @classmethod
    def type_check(cls, _context, value):
        _ = _context
        if not isinstance(value, cls):
            return TypeCheck(
                success=False, description=f"expected wrapper class {type(K8sOpMutatingOutput)}"
            )
        return TypeCheck(success=True)


class StepInputCacheKey(NamedTuple):
    step_key: str
    input_name: str


class K8sMutatingStepHandler(K8sStepHandler):
    """Specialized step handler that configure the next op based on the op metadata of the prior op."""

    op_mutation_enabled: bool
    step_input_cache: dict[StepInputCacheKey, UserDefinedDagsterK8sConfig]

    def __init__(
        self,
        image: str | None,
        container_context: K8sContainerContext,
        load_incluster_config: bool,
        kubeconfig_file: str | None,
        k8s_client_batch_api=None,
        op_mutation_enabled: bool = False,
    ):
        self.op_mutation_enabled = op_mutation_enabled
        self.step_input_cache = {}
        super().__init__(
            image, container_context, load_incluster_config, kubeconfig_file, k8s_client_batch_api
        )

    def _get_input_metadata(
        self, step_input: StepInput, step_context: StepOrchestrationContext
    ) -> Optional[UserDefinedDagsterK8sConfig]:
        # dagster type names should be garunteed unique, so this should be safe
        if step_input.dagster_type_key != K8sOpMutatingOutput.__name__:
            return {}
        step_cache_key = StepInputCacheKey(step_context.step.key, step_input.name)
        if step_cache_key in self.step_input_cache:
            step_context.log.debug(f"cache hit for key {step_cache_key}")
            return self.step_input_cache[step_cache_key]
        source = step_input.source
        if isinstance(source, FromPendingDynamicStepOutput):
            upstream_output_handle = source.step_output_handle
            # coerce FromPendingDynamicStepOutput to FromStepOutputSource
            source = source.resolve(upstream_output_handle.mapping_key)
        if not isinstance(source, FromStepOutput):
            return step_context.log.error(
                f"unable to consume {step_input.name}. FromStepOuput & FromPendingDynamicStepOutput sources supported, got {type(source)}"
            )
        if source.fan_in:
            return step_context.log.error("fan in step input not supported")
        job_def = step_context.job.get_definition()
        # lie, cheat, and steal. Create step execution context ahead of time
        step_run_ref = StepRunRef(
            run_config=job_def.run_config or {},
            dagster_run=step_context.dagster_run,
            run_id=step_context.run_id,
            step_key=step_context.step.key,
            retry_mode=step_context.retry_mode,
            recon_job=step_context.reconstructable_job,
            known_state=step_context.execution_plan.known_state,
        )
        step_exec_context = step_run_ref_to_step_context(step_run_ref, step_context.instance)
        input_def = job_def.get_op(step_context.step.node_handle).input_def_named(step_input.name)
        output_handle = source.step_output_handle
        # get requisite input manager
        if input_def.input_manager_key is not None:
            manager_key = input_def.input_manager_key
            input_manager = getattr(step_exec_context.resources, manager_key)
            check.invariant(
                isinstance(input_manager, InputManager),
                f'Input "{input_def.name}" for step "{step_context.step.key}" is depending on '
                f'the manager "{manager_key}" to load it, but it is not an InputManager. '
                "Please ensure that the resource returned for resource key "
                f'"{manager_key}" is an InputManager.',
            )
        else:
            manager_key = step_context.execution_plan.get_manager_key(
                source.step_output_handle, job_def
            )
            input_manager = step_exec_context.get_io_manager(output_handle)
            check.invariant(
                isinstance(input_manager, IOManager),
                f'Input "{input_def.name}" for step "{step_context.step.key}" is depending on '
                f'the manager of upstream output "{output_handle.output_name}" from step '
                f'"{output_handle.step_key}" to load it, but that manager is not an IOManager. '
                "Please ensure that the resource returned for resource key "
                f'"{manager_key}" is an IOManager.',
            )
        # load full input via input manager. DANGER, if value is excessively large this could have perf impacts on stephandler
        input_context = source.get_load_context(step_exec_context, input_def, manager_key)
        op_mutating_output: K8sOpMutatingOutput = input_manager.load_input(input_context)
        step_context.log.debug(f"eagerly recieved input {op_mutating_output}")
        self.step_input_cache[step_cache_key] = op_mutating_output.k8s_config
        return self.step_input_cache[step_cache_key]

    def _resolve_input_configs(
        self, step_handler_context: StepHandlerContext
    ) -> Optional[K8sContainerContext]:
        """Fetch all the configured k8s metadata for op inputs."""
        step_key = self._get_step_key(step_handler_context)
        step_context = step_handler_context.get_step_context(step_key)
        container_context = None
        for step_input in step_context.step.step_inputs:
            op_metadata_config = self._get_input_metadata(step_input, step_context)
            if not op_metadata_config:
                continue
            k8s_context = K8sContainerContext(run_k8s_config=op_metadata_config)
            if container_context is None:
                container_context = k8s_context
            else:
                container_context.merge(k8s_context)
        return container_context

    def _get_container_context(
        self, step_handler_context: StepHandlerContext
    ) -> K8sContainerContext:
        context = super()._get_container_context(step_handler_context)
        if not self.op_mutation_enabled:
            return context
        merged_input_k8s_configs = self._resolve_input_configs(step_handler_context)
        if merged_input_k8s_configs:
            return context.merge(merged_input_k8s_configs)
        return context

    def terminate_step(self, step_handler_context):
        yield from super().terminate_step(step_handler_context)
        # pop cache to save mem for steps we won't visit again
        step_key = self._get_step_key(step_handler_context)
        stale_cache_keys = [k for k in self.step_input_cache if k.step_key == step_key]
        for k in stale_cache_keys:
            self.step_input_cache.pop(k)


@executor(
    name="k8s_op_mutating",
    config_schema=_K8S_OP_EXECUTOR_CONFIG_SCHEMA,
    requirements=multiple_process_executor_requirements(),
)
def k8s_op_mutating_executor(init_context: InitExecutorContext) -> Executor:
    assert isinstance(init_context.instance.run_launcher, K8sRunLauncher)
    run_launcher = init_context.instance.run_launcher
    exc_cfg = init_context.executor_config
    k8s_container_context = K8sContainerContext(
        image_pull_policy=exc_cfg.get("image_pull_policy"),  # type: ignore
        image_pull_secrets=exc_cfg.get("image_pull_secrets"),  # type: ignore
        service_account_name=exc_cfg.get("service_account_name"),  # type: ignore
        env_config_maps=exc_cfg.get("env_config_maps"),  # type: ignore
        env_secrets=exc_cfg.get("env_secrets"),  # type: ignore
        env_vars=exc_cfg.get("env_vars"),  # type: ignore
        volume_mounts=exc_cfg.get("volume_mounts"),  # type: ignore
        volumes=exc_cfg.get("volumes"),  # type: ignore
        labels=exc_cfg.get("labels"),  # type: ignore
        namespace=exc_cfg.get("job_namespace"),  # type: ignore
        resources=exc_cfg.get("resources"),  # type: ignore
        scheduler_name=exc_cfg.get("scheduler_name"),  # type: ignore
        security_context=exc_cfg.get("security_context"),  # type: ignore
        # step_k8s_config feeds into the run_k8s_config field because it is merged
        # with any configuration for the run that was set on the run launcher or code location
        run_k8s_config=UserDefinedDagsterK8sConfig.from_dict(exc_cfg.get("step_k8s_config", {})),
    )
    if "load_incluster_config" in exc_cfg:
        load_incluster_config = cast(bool, exc_cfg["load_incluster_config"])
    else:
        load_incluster_config = run_launcher.load_incluster_config if run_launcher else True
    if "kubeconfig_file" in exc_cfg:
        kubeconfig_file = cast(Optional[str], exc_cfg["kubeconfig_file"])
    else:
        kubeconfig_file = run_launcher.kubeconfig_file if run_launcher else None
    op_mutation_enabled = exc_cfg.get("op_mutation_enabled", False)
    check.bool_param(op_mutation_enabled, "op_mutation_enabled")
    return StepDelegatingExecutor(
        K8sMutatingStepHandler(
            image=exc_cfg.get("job_image"),  # type: ignore
            container_context=k8s_container_context,
            load_incluster_config=load_incluster_config,
            kubeconfig_file=kubeconfig_file,
            op_mutation_enabled=op_mutation_enabled,
        ),
        retries=RetryMode.from_config(exc_cfg["retries"]),  # type: ignore
        max_concurrent=check.opt_int_elem(exc_cfg, "max_concurrent"),
        tag_concurrency_limits=check.opt_list_elem(exc_cfg, "tag_concurrency_limits"),
        should_verify_step=True,
    )
