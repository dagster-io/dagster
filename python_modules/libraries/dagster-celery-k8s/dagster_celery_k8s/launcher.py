import sys
from typing import cast

import kubernetes
from dagster_k8s.job import (
    DagsterK8sJobConfig,
    construct_dagster_k8s_job,
    get_job_name_from_run_id,
    get_user_defined_k8s_config,
)
from dagster_k8s.utils import delete_job

from dagster import DagsterInvariantViolationError, MetadataEntry
from dagster import _check as check
from dagster.config.field import resolve_to_config_type
from dagster.config.validate import process_config
from dagster.core.events import EngineEventData
from dagster.core.execution.retries import RetryMode
from dagster.core.launcher import LaunchRunContext, RunLauncher
from dagster.core.launcher.base import CheckRunHealthResult, WorkerStatus
from dagster.core.origin import PipelinePythonOrigin
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.core.storage.tags import DOCKER_IMAGE_TAG
from dagster.serdes import ConfigurableClass, ConfigurableClassData
from dagster.utils import frozentags, merge_dicts
from dagster.utils.error import serializable_error_info_from_exc_info

from .config import CELERY_K8S_CONFIG_KEY, celery_k8s_executor_config


class CeleryK8sRunLauncher(RunLauncher, ConfigurableClass):
    """In contrast to the :py:class:`K8sRunLauncher`, which launches dagster runs as single K8s
    Jobs, this run launcher is intended for use in concert with
    :py:func:`dagster_celery_k8s.celery_k8s_job_executor`.

    With this run launcher, execution is delegated to:

        1. A run worker Kubernetes Job, which traverses the dagster run execution plan and
           submits steps to Celery queues for execution;
        2. The step executions which are submitted to Celery queues are picked up by Celery workers,
           and each step execution spawns a step execution Kubernetes Job. See the implementation
           defined in :py:func:`dagster_celery_k8.executor.create_k8s_job_task`.

    You can configure a Dagster instance to use this RunLauncher by adding a section to your
    ``dagster.yaml`` like the following:

    .. code-block:: yaml

        run_launcher:
          module: dagster_k8s.launcher
          class: CeleryK8sRunLauncher
          config:
            instance_config_map: "dagster-k8s-instance-config-map"
            dagster_home: "/some/path"
            postgres_password_secret: "dagster-k8s-pg-password"
            broker: "some_celery_broker_url"
            backend: "some_celery_backend_url"

    """

    def __init__(
        self,
        instance_config_map,
        dagster_home,
        postgres_password_secret,
        load_incluster_config=True,
        kubeconfig_file=None,
        broker=None,
        backend=None,
        include=None,
        config_source=None,
        retries=None,
        inst_data=None,
        k8s_client_batch_api=None,
        env_config_maps=None,
        env_secrets=None,
        volume_mounts=None,
        volumes=None,
        service_account_name=None,
        image_pull_policy=None,
        image_pull_secrets=None,
        labels=None,
        fail_pod_on_run_failure=None,
    ):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

        if load_incluster_config:
            check.invariant(
                kubeconfig_file is None,
                "`kubeconfig_file` is set but `load_incluster_config` is True.",
            )
            kubernetes.config.load_incluster_config()
        else:
            check.opt_str_param(kubeconfig_file, "kubeconfig_file")
            kubernetes.config.load_kube_config(kubeconfig_file)

        self._fixed_batch_api = k8s_client_batch_api

        self.instance_config_map = check.str_param(instance_config_map, "instance_config_map")
        self.dagster_home = check.str_param(dagster_home, "dagster_home")
        self.postgres_password_secret = check.str_param(
            postgres_password_secret, "postgres_password_secret"
        )
        self.broker = check.opt_str_param(broker, "broker")
        self.backend = check.opt_str_param(backend, "backend")
        self.include = check.opt_list_param(include, "include")
        self.config_source = check.opt_dict_param(config_source, "config_source")

        retries = check.opt_dict_param(retries, "retries") or {"enabled": {}}
        self.retries = RetryMode.from_config(retries)

        self._env_config_maps = check.opt_list_param(
            env_config_maps, "env_config_maps", of_type=str
        )
        self._env_secrets = check.opt_list_param(env_secrets, "env_secrets", of_type=str)

        self._volume_mounts = check.opt_list_param(volume_mounts, "volume_mounts")
        self._volumes = check.opt_list_param(volumes, "volumes")

        self._service_account_name = check.opt_str_param(
            service_account_name, "service_account_name"
        )
        self._image_pull_policy = check.opt_str_param(
            image_pull_policy, "image_pull_policy", "IfNotPresent"
        )
        self._image_pull_secrets = check.opt_list_param(
            image_pull_secrets, "image_pull_secrets", of_type=dict
        )
        self._labels = check.opt_dict_param(labels, "labels", key_type=str, value_type=str)
        self._fail_pod_on_run_failure = check.opt_bool_param(
            fail_pod_on_run_failure, "fail_pod_on_run_failure"
        )

        super().__init__()

    @property
    def _batch_api(self):
        return self._fixed_batch_api if self._fixed_batch_api else kubernetes.client.BatchV1Api()

    @classmethod
    def config_type(cls):
        from dagster_celery.executor import CELERY_CONFIG

        return merge_dicts(DagsterK8sJobConfig.config_type_run_launcher(), CELERY_CONFIG)

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data, **config_value)

    @property
    def inst_data(self):
        return self._inst_data

    def launch_run(self, context: LaunchRunContext) -> None:
        run = context.pipeline_run

        job_name = get_job_name_from_run_id(run.run_id)
        pod_name = job_name
        exc_config = _get_validated_celery_k8s_executor_config(run.run_config)
        env_vars = None

        job_image_from_executor_config = exc_config.get("job_image")

        pipeline_origin = cast(PipelinePythonOrigin, context.pipeline_code_origin)
        repository_origin = pipeline_origin.repository_origin

        job_image = repository_origin.container_image

        if job_image:
            if job_image_from_executor_config:
                job_image = job_image_from_executor_config
                self._instance.report_engine_event(
                    f"You have specified a job_image {job_image_from_executor_config} in your executor configuration, "
                    f"but also {job_image} in your user-code deployment. Using the job image {job_image_from_executor_config} "
                    f"from executor configuration as it takes precedence.",
                    run,
                    cls=self.__class__,
                )
        else:
            if not job_image_from_executor_config:
                raise DagsterInvariantViolationError(
                    "You have not specified a job_image in your executor configuration. "
                    "To resolve this error, specify the job_image configuration in the executor "
                    "config section in your run config. \n"
                    "Note: You may also be seeing this error because you are using the configured API. "
                    "Using configured with the celery-k8s executor is not supported at this time, "
                    "and the job_image must be configured at the top-level executor config without "
                    "using configured."
                )

            job_image = job_image_from_executor_config

        job_config = self.get_k8s_job_config(job_image, exc_config)

        self._instance.add_run_tags(
            run.run_id,
            {DOCKER_IMAGE_TAG: job_config.job_image},
        )

        user_defined_k8s_config = get_user_defined_k8s_config(frozentags(run.tags))

        from dagster.cli.api import ExecuteRunArgs

        run_args = ExecuteRunArgs(
            pipeline_origin=pipeline_origin,
            pipeline_run_id=run.run_id,
            instance_ref=self._instance.get_ref(),
            set_exit_code_on_failure=self._fail_pod_on_run_failure,
        ).get_command_args()

        job = construct_dagster_k8s_job(
            job_config,
            args=run_args,
            job_name=job_name,
            pod_name=pod_name,
            component="run_worker",
            user_defined_k8s_config=user_defined_k8s_config,
            env_vars=env_vars,
            labels={
                "dagster/job": pipeline_origin.pipeline_name,
                "dagster/run-id": run.run_id,
            },
        )

        job_namespace = exc_config.get("job_namespace")

        self._instance.report_engine_event(
            "Creating Kubernetes run worker job",
            run,
            EngineEventData(
                [
                    MetadataEntry("Kubernetes Job name", value=job_name),
                    MetadataEntry("Kubernetes Namespace", value=job_namespace),
                    MetadataEntry("Run ID", value=run.run_id),
                ]
            ),
            cls=self.__class__,
        )

        self._batch_api.create_namespaced_job(body=job, namespace=job_namespace)
        self._instance.report_engine_event(
            "Kubernetes run worker job created",
            run,
            EngineEventData(
                [
                    MetadataEntry("Kubernetes Job name", value=job_name),
                    MetadataEntry("Kubernetes Namespace", value=job_namespace),
                    MetadataEntry("Run ID", value=run.run_id),
                ]
            ),
            cls=self.__class__,
        )

    def get_k8s_job_config(self, job_image, exc_config):
        return DagsterK8sJobConfig(
            dagster_home=self.dagster_home,
            instance_config_map=self.instance_config_map,
            postgres_password_secret=self.postgres_password_secret,
            job_image=check.opt_str_param(job_image, "job_image"),
            image_pull_policy=exc_config.get("image_pull_policy", self._image_pull_policy),
            image_pull_secrets=exc_config.get("image_pull_secrets", []) + self._image_pull_secrets,
            service_account_name=exc_config.get("service_account_name", self._service_account_name),
            env_config_maps=exc_config.get("env_config_maps", []) + self._env_config_maps,
            env_secrets=exc_config.get("env_secrets", []) + self._env_secrets,
            volume_mounts=exc_config.get("volume_mounts", []) + self._volume_mounts,
            volumes=exc_config.get("volumes", []) + self._volumes,
            labels=merge_dicts(self._labels, exc_config.get("labels", {})),
        )

    # https://github.com/dagster-io/dagster/issues/2741
    def can_terminate(self, run_id):
        check.str_param(run_id, "run_id")

        pipeline_run = self._instance.get_run_by_id(run_id)
        if not pipeline_run:
            return False

        if pipeline_run.status != PipelineRunStatus.STARTED:
            return False

        return True

    def terminate(self, run_id):
        check.str_param(run_id, "run_id")

        run = self._instance.get_run_by_id(run_id)
        if not run:
            return False

        can_terminate = self.can_terminate(run_id)
        if not can_terminate:
            self._instance.report_engine_event(
                message="Unable to terminate dagster job: can_terminate returned {}.".format(
                    can_terminate
                ),
                pipeline_run=run,
                cls=self.__class__,
            )
            return False

        job_name = get_job_name_from_run_id(run_id)

        job_namespace = self.get_namespace_from_run_config(run_id)

        self._instance.report_run_canceling(run)

        try:
            termination_result = delete_job(job_name=job_name, namespace=job_namespace)
            if termination_result:
                self._instance.report_engine_event(
                    message="Dagster Job was terminated successfully.",
                    pipeline_run=run,
                    cls=self.__class__,
                )
            else:
                self._instance.report_engine_event(
                    message="Dagster Job was not terminated successfully; delete_job returned {}".format(
                        termination_result
                    ),
                    pipeline_run=run,
                    cls=self.__class__,
                )
            return termination_result
        except Exception:
            self._instance.report_engine_event(
                message="Dagster Job was not terminated successfully; encountered error in delete_job",
                pipeline_run=run,
                engine_event_data=EngineEventData.engine_error(
                    serializable_error_info_from_exc_info(sys.exc_info())
                ),
                cls=self.__class__,
            )

    def get_namespace_from_run_config(self, run_id):
        check.str_param(run_id, "run_id")

        pipeline_run = self._instance.get_run_by_id(run_id)
        run_config = pipeline_run.run_config
        executor_config = _get_validated_celery_k8s_executor_config(run_config)
        return executor_config.get("job_namespace")

    @property
    def supports_check_run_worker_health(self):
        return True

    def check_run_worker_health(self, run: PipelineRun):
        job_namespace = _get_validated_celery_k8s_executor_config(run.run_config).get(
            "job_namespace"
        )
        job_name = get_job_name_from_run_id(run.run_id)
        try:
            job = self._batch_api.read_namespaced_job(namespace=job_namespace, name=job_name)
        except Exception:
            return CheckRunHealthResult(
                WorkerStatus.UNKNOWN, str(serializable_error_info_from_exc_info(sys.exc_info()))
            )
        if job.status.failed:
            return CheckRunHealthResult(WorkerStatus.FAILED, "K8s job failed")
        return CheckRunHealthResult(WorkerStatus.RUNNING)


def _get_validated_celery_k8s_executor_config(run_config):
    check.dict_param(run_config, "run_config")

    executor_config = run_config.get("execution", {})
    execution_config_schema = resolve_to_config_type(celery_k8s_executor_config())

    # In run config on jobs, we don't have an executor key
    if not CELERY_K8S_CONFIG_KEY in executor_config:

        execution_run_config = executor_config.get("config", {})
    else:
        execution_run_config = (run_config["execution"][CELERY_K8S_CONFIG_KEY] or {}).get(
            "config", {}
        )

    res = process_config(execution_config_schema, execution_run_config)

    check.invariant(
        res.success,
        "Incorrect execution schema provided. Note: You may also be seeing this error "
        "because you are using the configured API. "
        "Using configured with the {config_key} executor is not supported at this time, "
        "and all executor config must be directly in the run config without using configured.".format(
            config_key=CELERY_K8S_CONFIG_KEY,
        ),
    )

    return res.value
