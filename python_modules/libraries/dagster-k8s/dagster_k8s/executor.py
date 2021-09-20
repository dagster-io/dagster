import kubernetes
from dagster import Field, StringSource, check, executor
from dagster.core.definitions.executor import multiple_process_executor_requirements
from dagster.core.errors import DagsterUnmetExecutorRequirementsError
from dagster.core.events import DagsterEvent, DagsterEventType, EngineEventData, EventMetadataEntry
from dagster.core.execution.plan.objects import StepFailureData
from dagster.core.execution.retries import get_retries_config
from dagster.core.executor.base import Executor
from dagster.core.executor.init import InitExecutorContext
from dagster.core.executor.step_delegating import StepDelegatingExecutor
from dagster.core.executor.step_delegating.step_handler import StepHandler
from dagster.core.executor.step_delegating.step_handler.base import StepHandlerContext
from dagster.core.types.dagster_type import Optional
from dagster.serdes.serdes import serialize_dagster_namedtuple
from dagster.utils import frozentags, merge_dicts
from dagster.utils.backcompat import experimental
from dagster_k8s.launcher import K8sRunLauncher

from .job import (
    DagsterK8sJobConfig,
    construct_dagster_k8s_job,
    get_k8s_job_name,
    get_user_defined_k8s_config,
)
from .utils import delete_job


@executor(
    name="k8s",
    config_schema=merge_dicts(
        DagsterK8sJobConfig.config_type_pipeline_run(),
        {"job_namespace": Field(StringSource, is_required=False)},
        {"retries": get_retries_config()},
    ),
    requirements=multiple_process_executor_requirements(),
)
@experimental
def k8s_job_executor(init_context: InitExecutorContext) -> Executor:
    """
    Executor which launches steps as Kubernetes Jobs. This executor is experimental.

    To add the Kubernetes Job executor in addition to the
    :py:class:`~dagster.default_executors`, you should add it to the ``executor_defs`` defined on a
    :py:class:`~dagster.ModeDefinition` as follows:

    .. literalinclude:: ../../../../../../python_modules/libraries/dagster-k8s/dagster_k8s_tests/unit_tests/test_example_executor_mode_def.py
       :start-after: start_marker
       :end-before: end_marker
       :language: python

    Then you can configure the executor with run config (either via a :py:class:`~dagster.PresetDefinition` or the Dagit playground) as follows:

    .. code-block:: YAML

        execution:
          k8s:
            config:
              job_namespace: 'some-namespace'
              image_pull_policy: ...
              image_pull_secrets: ...
              service_account_name: ...
              env_config_maps: ...
              env_secrets: ...
              job_image: ... # leave out if using userDeployments
    """

    run_launcher = init_context.instance.run_launcher
    if not isinstance(run_launcher, K8sRunLauncher):
        raise DagsterUnmetExecutorRequirementsError(
            "This engine is only compatible with a K8sRunLauncher; configure the "
            "K8sRunLauncher on your instance to use it.",
        )

    exc_cfg = init_context.executor_config
    job_config = DagsterK8sJobConfig(
        dagster_home=run_launcher.dagster_home,
        instance_config_map=run_launcher.instance_config_map,
        postgres_password_secret=run_launcher.postgres_password_secret,
        job_image=exc_cfg.get("job_image"),
        image_pull_policy=(
            exc_cfg.get("image_pull_policy")
            if exc_cfg.get("image_pull_policy") != None
            else run_launcher.image_pull_policy
        ),
        image_pull_secrets=run_launcher.image_pull_secrets
        + (exc_cfg.get("image_pull_secrets") or []),
        service_account_name=(
            exc_cfg.get("service_account_name")
            if exc_cfg.get("service_account_name") != None
            else run_launcher.service_account_name
        ),
        env_config_maps=run_launcher.env_config_maps + (exc_cfg.get("env_config_maps") or []),
        env_secrets=run_launcher.env_secrets + (exc_cfg.get("env_secrets") or []),
    )

    return StepDelegatingExecutor(
        K8sStepHandler(
            job_config=job_config,
            job_namespace=(
                exc_cfg.get("job_namespace")
                if exc_cfg.get("job_namespace") != None
                else run_launcher.job_namespace
            ),
            load_incluster_config=run_launcher.load_incluster_config,
            kubeconfig_file=run_launcher.kubeconfig_file,
        )
    )


@experimental
class K8sStepHandler(StepHandler):
    @property
    def name(self):
        return "K8sStepHandler"

    def __init__(
        self,
        job_config: DagsterK8sJobConfig,
        job_namespace: str,
        load_incluster_config: bool,
        kubeconfig_file: Optional[str],
        k8s_client_batch_api=None,
    ):
        super().__init__()

        self._job_config = job_config
        self._job_namespace = job_namespace
        self._fixed_k8s_client_batch_api = k8s_client_batch_api

        if load_incluster_config:
            check.invariant(
                kubeconfig_file is None,
                "`kubeconfig_file` is set but `load_incluster_config` is True.",
            )
            kubernetes.config.load_incluster_config()
        else:
            check.opt_str_param(kubeconfig_file, "kubeconfig_file")
            kubernetes.config.load_kube_config(kubeconfig_file)

    @property
    def _batch_api(self):
        return self._fixed_k8s_client_batch_api or kubernetes.client.BatchV1Api()

    def launch_step(self, step_handler_context: StepHandlerContext):
        events = []

        assert (
            len(step_handler_context.execute_step_args.step_keys_to_execute) == 1
        ), "Launching multiple steps is not currently supported"
        step_key = step_handler_context.execute_step_args.step_keys_to_execute[0]

        k8s_name_key = get_k8s_job_name(
            step_handler_context.execute_step_args.pipeline_run_id,
            step_key,
        )
        job_name = "dagster-job-%s" % (k8s_name_key)
        pod_name = "dagster-job-%s" % (k8s_name_key)

        input_json = serialize_dagster_namedtuple(step_handler_context.execute_step_args)
        args = ["dagster", "api", "execute_step", input_json]

        job_config = self._job_config
        if not job_config.job_image:
            job_config = job_config.with_image(
                step_handler_context.execute_step_args.pipeline_origin.repository_origin.container_image
            )

        if not job_config.job_image:
            raise Exception("No image included in either executor config or the pipeline")

        user_defined_k8s_config = get_user_defined_k8s_config(
            frozentags(step_handler_context.step_tags[step_key])
        )

        job = construct_dagster_k8s_job(
            job_config=job_config,
            args=args,
            job_name=job_name,
            pod_name=pod_name,
            component="step_worker",
            user_defined_k8s_config=user_defined_k8s_config,
        )

        events.append(
            DagsterEvent(
                event_type_value=DagsterEventType.ENGINE_EVENT.value,
                pipeline_name=step_handler_context.execute_step_args.pipeline_origin.pipeline_name,
                step_key=step_key,
                message=f"Executing step {step_key} in Kubernetes job {job_name}",
                event_specific_data=EngineEventData(
                    [
                        EventMetadataEntry.text(step_key, "Step key"),
                        EventMetadataEntry.text(job_name, "Kubernetes Job name"),
                    ],
                ),
            )
        )

        self._batch_api.create_namespaced_job(body=job, namespace=self._job_namespace)

        return events

    def check_step_health(self, step_handler_context: StepHandlerContext):
        assert (
            len(step_handler_context.execute_step_args.step_keys_to_execute) == 1
        ), "Launching multiple steps is not currently supported"
        step_key = step_handler_context.execute_step_args.step_keys_to_execute[0]

        k8s_name_key = get_k8s_job_name(
            step_handler_context.execute_step_args.pipeline_run_id,
            step_key,
        )
        job_name = "dagster-job-%s" % (k8s_name_key)

        job = self._batch_api.read_namespaced_job(namespace=self._job_namespace, name=job_name)
        if job.status.failed:
            return [
                DagsterEvent(
                    event_type_value=DagsterEventType.STEP_FAILURE.value,
                    pipeline_name=step_handler_context.execute_step_args.pipeline_origin.pipeline_name,
                    step_key=step_key,
                    message=f"Discovered failed Kubernetes job {job_name} for step {step_key}",
                    event_specific_data=StepFailureData(
                        error=None,
                        user_failure_data=None,
                    ),
                )
            ]
        return []

    def terminate_step(self, step_handler_context: StepHandlerContext):
        assert (
            len(step_handler_context.execute_step_args.step_keys_to_execute) == 1
        ), "Launching multiple steps is not currently supported"
        step_key = step_handler_context.execute_step_args.step_keys_to_execute[0]

        k8s_name_key = get_k8s_job_name(
            step_handler_context.execute_step_args.pipeline_run_id,
            step_key,
        )
        job_name = "dagster-job-%s" % (k8s_name_key)

        delete_job(job_name=job_name, namespace=self._job_namespace)
        return []
