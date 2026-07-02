from collections.abc import Mapping
from typing import Any, Generic, Optional, TypeVar, Union, cast

from dagster import (
    DagsterEventType,
    DynamicOutput,
    Field,
    JsonMetadataValue,
    Output,
    executor,
    usable_as_dagster_type,
)
from dagster._core.definitions.executor_definition import multiple_process_executor_requirements
from dagster._core.definitions.utils import DEFAULT_OUTPUT
from dagster._core.execution.context.system import StepOrchestrationContext
from dagster._core.execution.plan.handle import ResolvedFromDynamicStepHandle, StepHandle
from dagster._core.execution.plan.inputs import (
    FromPendingDynamicStepOutput,
    FromStepOutput,
    StepInput,
)
from dagster._core.execution.plan.outputs import StepOutputData, StepOutputHandle
from dagster._core.execution.retries import RetryMode
from dagster._core.executor.base import Executor
from dagster._core.executor.init import InitExecutorContext
from dagster._core.executor.step_delegating import StepDelegatingExecutor, StepHandlerContext
from dagster._core.storage.event_log import SqlEventLogStorage
from dagster._utils.merger import merge_dicts
from dagster_shared import check

from dagster_k8s.container_context import K8sContainerContext
from dagster_k8s.executor import _K8S_EXECUTOR_CONFIG_SCHEMA, K8sStepHandler
from dagster_k8s.job import USER_DEFINED_K8S_CONFIG_KEY, UserDefinedDagsterK8sConfig
from dagster_k8s.launcher import K8sRunLauncher

_K8S_OP_EXECUTOR_CONFIG_SCHEMA = merge_dicts(
    _K8S_EXECUTOR_CONFIG_SCHEMA,
    {
        "op_mutation_enabled": Field(
            bool,
            default_value=True,
            description="enabled op configuration based on output of prior op",
        )
    },
)

USER_DEFINED_INPUT_K8S_OP_MUTATION_KEY = "dagster-k8s/mutation-enabled"


T = TypeVar("T")


@usable_as_dagster_type
class K8sOpMutatingWrapper(Generic[T]):
    value: T

    def __init__(self, value: T):
        self.value = value

    @classmethod
    def name(cls) -> str:
        return cls.__name__


def coerce_k8s_configs(
    k8s_config: Union[UserDefinedDagsterK8sConfig, Mapping[str, Any]],
) -> UserDefinedDagsterK8sConfig:
    if isinstance(k8s_config, UserDefinedDagsterK8sConfig):
        return k8s_config
    check.mapping_param(k8s_config, "k8s_config", str)
    return UserDefinedDagsterK8sConfig.from_dict(k8s_config)


class K8sMutatingOutput(Output, Generic[T]):
    def __init__(
        self,
        value: T,
        k8s_config: Union[UserDefinedDagsterK8sConfig, Mapping[str, Any]],
        output_name: str = DEFAULT_OUTPUT,
    ):
        k8s_config = coerce_k8s_configs(k8s_config)
        super().__init__(
            value,
            output_name,
            metadata={USER_DEFINED_K8S_CONFIG_KEY: JsonMetadataValue(k8s_config.to_dict())},
        )


class K8sMutatingDynamicOutput(DynamicOutput, Generic[T]):
    def __init__(
        self,
        value: T,
        mapping_key: str,
        k8s_config: Union[UserDefinedDagsterK8sConfig, Mapping[str, Any]],
        output_name: str = DEFAULT_OUTPUT,
    ):
        k8s_config = coerce_k8s_configs(k8s_config)
        super().__init__(
            value,
            mapping_key,
            output_name,
            metadata={USER_DEFINED_K8S_CONFIG_KEY: JsonMetadataValue(k8s_config.to_dict())},
        )


def get_upstream_output_record(
    event_log: SqlEventLogStorage, output_handle: StepOutputHandle, run_id: str
) -> Optional[StepOutputData]:
    """Fetch step output record given a particular output handle."""
    upstream_record: Optional[StepOutputData] = None
    has_more = True
    batch_limit = 1_000
    cursor = None

    while upstream_record is None and has_more:
        record_conn = event_log.get_records_for_run(
            run_id, cursor, DagsterEventType.STEP_OUTPUT, batch_limit
        )
        has_more = record_conn.has_more
        cursor = record_conn.cursor
        step_output_events = (
            e.get_dagster_event().step_output_data
            for e in map(lambda r: r.event_log_entry, record_conn.records)
            if e.step_key == output_handle.step_key
            and e.is_dagster_event
            and e.get_dagster_event().is_successful_output
        )
        upstream_record = next(
            (output for output in step_output_events if output.step_output_handle == output_handle),
            None,
        )
    return upstream_record


def walk_runs_for_output_record(
    step_context: StepOrchestrationContext, output_handle: StepOutputHandle
) -> Optional[StepOutputData]:
    """Upon a retry, dagster will launch a new run. Walk the run and it's corresponding parents for the latest output step."""
    event_log = step_context.instance.event_log_storage
    if not isinstance(event_log, SqlEventLogStorage):
        return step_context.log.error(
            f"can only use executor with log type {type(SqlEventLogStorage)}"
        )
    instance = step_context.instance
    run_id = step_context.dagster_run.run_id
    while run_id:
        output_record = get_upstream_output_record(event_log, output_handle, run_id)
        if output_record:
            return output_record
        dagster_run = instance.get_run_by_id(run_id)
        if dagster_run is None:
            return step_context.log.error(f"failure to find run: {run_id}")
        run_id = dagster_run.parent_run_id
    return None


class K8sMutatingStepHandler(K8sStepHandler):
    """Specialized step handler that configure the next op based on the op metadata of the prior op."""

    op_mutation_enabled: bool
    container_ctx_cache: dict[Union[StepHandle, ResolvedFromDynamicStepHandle], K8sContainerContext]

    def __init__(
        self,
        image: Optional[str],
        container_context: K8sContainerContext,
        load_incluster_config: bool,
        kubeconfig_file: Optional[str],
        k8s_client_batch_api=None,
        per_step_k8s_config=None,
        op_mutation_enabled: bool = False,
    ):
        self.op_mutation_enabled = op_mutation_enabled
        self.container_ctx_cache = {}
        super().__init__(
            image=image,
            container_context=container_context,
            load_incluster_config=load_incluster_config,
            kubeconfig_file=kubeconfig_file,
            k8s_client_batch_api=k8s_client_batch_api,
            per_step_k8s_config=per_step_k8s_config,
        )

    @property
    def name(self) -> str:
        return "K8sMutatingStepHandler"

    def _get_input_metadata(
        self, step_input: StepInput, step_context: StepOrchestrationContext
    ) -> Optional[UserDefinedDagsterK8sConfig]:
        # dagster type names should be garunteed unique, so this should be safe.
        job_def = step_context.job.get_definition()
        input_def = job_def.get_op(step_context.step.node_handle).input_def_named(step_input.name)
        input_mutation_enabled = False
        input_metadata = input_def.metadata
        if USER_DEFINED_INPUT_K8S_OP_MUTATION_KEY in input_metadata:
            input_mutation_enabled = check.bool_elem(
                input_metadata,
                USER_DEFINED_INPUT_K8S_OP_MUTATION_KEY,
                f"{USER_DEFINED_INPUT_K8S_OP_MUTATION_KEY} must be a bool",
            )
        input_mutation_enabled |= step_input.dagster_type_key == K8sOpMutatingWrapper.name()
        if not input_mutation_enabled:
            return None
        source = step_input.source
        if isinstance(source, FromPendingDynamicStepOutput):
            upstream_output_handle = source.step_output_handle
            # coerce FromPendingDynamicStepOutput to FromStepOutputSource
            assert isinstance(upstream_output_handle.mapping_key, str)
            source = source.resolve(upstream_output_handle.mapping_key)
        if not isinstance(source, FromStepOutput):
            return step_context.log.error(
                f"unable to consume {step_input.name}. FromStepOuput & FromPendingDynamicStepOutput sources supported, got {type(source)}"
            )
        if source.fan_in:
            return step_context.log.error("fan in step input not supported")
        output_handle = source.step_output_handle
        upstream_record = walk_runs_for_output_record(step_context, output_handle)
        if upstream_record is None:
            return step_context.log.error(
                f"unable to find output event for input {step_input.name}"
            )
        # should be garunteed, so make ruff happy (TCH002)
        check.inst(upstream_record, StepOutputData)
        if USER_DEFINED_K8S_CONFIG_KEY not in upstream_record.metadata:
            return step_context.log.warning(
                f"upstream ouput {output_handle} has no metadata key {USER_DEFINED_K8S_CONFIG_KEY}"
            )
        k8s_config_md = upstream_record.metadata[USER_DEFINED_K8S_CONFIG_KEY]
        if not isinstance(k8s_config_md, JsonMetadataValue):
            return step_context.log.error(
                f"user defined config metatdata need to be of type {JsonMetadataValue}, got {type(k8s_config_md)}"
            )
        source_output_msg = f'using output metadata from output "{output_handle.output_name}"'
        if output_handle.mapping_key:
            source_output_msg += f' with mapping key "{output_handle.mapping_key}"'
        step_context.log.info(
            f'{source_output_msg} from step "{output_handle.step_key}" to mutate op k8s config'
        )
        return UserDefinedDagsterK8sConfig.from_dict(k8s_config_md.data)

    def _merge_input_configs(self, step_handler_context: StepHandlerContext) -> K8sContainerContext:
        """Fetch all the configured k8s metadata for op inputs."""
        step_key = self._get_step_key(step_handler_context)
        step_context = cast(
            "StepOrchestrationContext", step_handler_context.get_step_context(step_key)
        )
        k8s_context = super()._get_container_context(step_handler_context)
        for step_input in step_context.step.step_inputs:
            op_metadata_config = self._get_input_metadata(step_input, step_context)
            if op_metadata_config:
                k8s_context = k8s_context.merge(
                    K8sContainerContext(run_k8s_config=op_metadata_config)
                )

        return k8s_context

    def _get_container_context(
        self, step_handler_context: StepHandlerContext
    ) -> K8sContainerContext:
        step_key = self._get_step_key(step_handler_context)
        step_context = step_handler_context.get_step_context(step_key)
        if not self.op_mutation_enabled:
            step_context.log.warning("using op mutating executor with op mutation disabled")
            return super()._get_container_context(step_handler_context)
        step_handle = step_context.step.handle
        if step_handle in self.container_ctx_cache:
            return self.container_ctx_cache[step_handle]
        self.container_ctx_cache[step_handle] = self._merge_input_configs(step_handler_context)
        return self.container_ctx_cache[step_handle]

    def terminate_step(self, step_handler_context: StepHandlerContext):
        try:
            yield from super().terminate_step(step_handler_context)
        finally:
            # pop cache to save mem for steps we won't visit again
            step_key = self._get_step_key(step_handler_context)
            step_context = step_handler_context.get_step_context(step_key)
            # entry might not exist if op mutation is disabled
            self.container_ctx_cache.pop(step_context.step.handle, None)


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
        load_incluster_config = cast("bool", exc_cfg["load_incluster_config"])
    else:
        load_incluster_config = run_launcher.load_incluster_config if run_launcher else True
    if "kubeconfig_file" in exc_cfg:
        kubeconfig_file = cast("Optional[str]", exc_cfg["kubeconfig_file"])
    else:
        kubeconfig_file = run_launcher.kubeconfig_file if run_launcher else None
    op_mutation_enabled = check.bool_elem(exc_cfg, "op_mutation_enabled")
    return StepDelegatingExecutor(
        K8sMutatingStepHandler(
            image=exc_cfg.get("job_image"),  # type: ignore
            container_context=k8s_container_context,
            load_incluster_config=load_incluster_config,
            kubeconfig_file=kubeconfig_file,
            per_step_k8s_config=exc_cfg.get("per_step_k8s_config", {}),
            op_mutation_enabled=op_mutation_enabled,
        ),
        retries=RetryMode.from_config(exc_cfg["retries"]),  # type: ignore
        max_concurrent=check.opt_int_elem(exc_cfg, "max_concurrent"),
        tag_concurrency_limits=check.opt_list_elem(exc_cfg, "tag_concurrency_limits"),
        should_verify_step=True,
    )
