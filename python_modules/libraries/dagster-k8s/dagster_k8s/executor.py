import os
from typing import List

import kubernetes
from dagster import Field, StringSource, executor
from dagster.core.definitions.executor import multiple_process_executor_requirements
from dagster.core.events import DagsterEvent
from dagster.core.execution.context.system import IStepContext
from dagster.core.execution.plan.objects import StepFailureData
from dagster.core.execution.plan.state import KnownExecutionState
from dagster.core.execution.retries import RetryMode, get_retries_config
from dagster.core.executor.base import Executor
from dagster.core.executor.init import InitExecutorContext
from dagster.core.executor.step_delegating import StepDelegatingExecutor
from dagster.core.executor.step_delegating.step_handler import StepHandler
from dagster.grpc.types import ExecuteStepArgs
from dagster.serdes.serdes import serialize_dagster_namedtuple
from dagster.utils import frozentags, merge_dicts
from dagster_k8s.job import (
    DagsterK8sJobConfig,
    construct_dagster_k8s_job,
    get_k8s_job_name,
    get_user_defined_k8s_config,
)


class K8sStepHandler(StepHandler):
    @property
    def name(self):
        return "K8sStepHandler"

    def __init__(
        self,
        retries: RetryMode,
        job_config: DagsterK8sJobConfig,
        job_namespace: str,
    ):
        super().__init__(retries)

        self._job_config = job_config
        self._job_namespace = job_namespace

    def launch_steps(
        self,
        step_contexts: List[IStepContext],
        known_state: KnownExecutionState,
    ):
        assert len(step_contexts) == 1, "Launching multiple steps is not currently supported"
        step_context = step_contexts[0]

        k8s_name_key = get_k8s_job_name(
            self.pipeline_context.plan_data.pipeline_run.run_id,
            step_context.step.key,
        )
        job_name = "dagster-job-%s" % (k8s_name_key)
        pod_name = "dagster-job-%s" % (k8s_name_key)

        execute_step_args = ExecuteStepArgs(
            pipeline_origin=self.pipeline_context.reconstructable_pipeline.get_python_origin(),
            pipeline_run_id=self.pipeline_context.pipeline_run.run_id,
            step_keys_to_execute=[step_context.step.key],
            instance_ref=self.pipeline_context.instance.get_ref(),
            retry_mode=self.retries.for_inner_plan(),
            known_state=known_state,
            should_verify_step=True,
        )

        input_json = serialize_dagster_namedtuple(execute_step_args)
        args = ["dagster", "api", "execute_step", input_json]

        job = construct_dagster_k8s_job(
            self._job_config,
            args,
            job_name,
            get_user_defined_k8s_config(frozentags()),
            pod_name,
        )

        kubernetes.config.load_incluster_config()
        kubernetes.client.BatchV1Api().create_namespaced_job(
            body=job, namespace=self._job_namespace
        )

    def check_step_health(
        self,
        step_contexts: List[IStepContext],
        known_state: KnownExecutionState,
    ):
        assert len(step_contexts) == 1, "Checking multiple steps is not currently supported"
        step_context = step_contexts[0]

        k8s_name_key = get_k8s_job_name(
            self.pipeline_context.plan_data.pipeline_run.run_id,
            step_context.step.key,
        )
        job_name = "dagster-job-%s" % (k8s_name_key)

        job = kubernetes.client.BatchV1Api().read_namespaced_job(
            namespace=self._job_namespace, name=job_name
        )
        if job.status.failed:
            step_failure_event = DagsterEvent.step_failure_event(
                step_context=step_context,
                step_failure_data=StepFailureData(error=None, user_failure_data=None),
            )

            return [step_failure_event]
        return []

    def terminate_steps(self, step_keys: List[str]):
        raise NotImplementedError()


@executor(
    name="k8s",
    config_schema=merge_dicts(
        DagsterK8sJobConfig.config_type_pipeline_run(),
        {
            "job_namespace": Field(
                StringSource,
                is_required=False,
                default_value="default",
            )
        },
        {"retries": get_retries_config()},
    ),
    requirements=multiple_process_executor_requirements(),
)
def dagster_k8s_executor(init_context: InitExecutorContext) -> Executor:
    run_launcher = init_context.instance.run_launcher
    exc_cfg = init_context.executor_config
    job_config = DagsterK8sJobConfig(
        dagster_home=run_launcher.dagster_home,
        instance_config_map=run_launcher.instance_config_map,
        postgres_password_secret=run_launcher.postgres_password_secret,
        job_image=exc_cfg.get("job_image") or os.getenv("DAGSTER_CURRENT_IMAGE"),
        image_pull_policy=exc_cfg.get("image_pull_policy"),
        image_pull_secrets=exc_cfg.get("image_pull_secrets"),
        service_account_name=exc_cfg.get("service_account_name"),
        env_config_maps=exc_cfg.get("env_config_maps"),
        env_secrets=exc_cfg.get("env_secrets"),
    )

    return StepDelegatingExecutor(
        K8sStepHandler(
            retries=RetryMode.DISABLED,  # Not currently supported
            job_config=job_config,
            job_namespace=exc_cfg.get("job_namespace"),
        )
    )
