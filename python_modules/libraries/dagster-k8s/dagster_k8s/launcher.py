import sys
from typing import Mapping, Optional, Sequence

import kubernetes

from dagster import Field, MetadataEntry, StringSource
from dagster import _check as check
from dagster._cli.api import ExecuteRunArgs
from dagster._core.events import EngineEventData
from dagster._core.launcher import LaunchRunContext, ResumeRunContext, RunLauncher
from dagster._core.launcher.base import CheckRunHealthResult, WorkerStatus
from dagster._core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster._core.storage.tags import DOCKER_IMAGE_TAG
from dagster._grpc.types import ResumeRunArgs
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from dagster._utils import frozentags, merge_dicts
from dagster._utils.error import serializable_error_info_from_exc_info

from .container_context import K8sContainerContext
from .job import (
    DagsterK8sJobConfig,
    construct_dagster_k8s_job,
    get_job_name_from_run_id,
    get_user_defined_k8s_config,
)
from .utils import delete_job


class K8sRunLauncher(RunLauncher, ConfigurableClass):
    """RunLauncher that starts a Kubernetes Job for each Dagster job run.

    Encapsulates each run in a separate, isolated invocation of ``dagster-graphql``.

    You can configure a Dagster instance to use this RunLauncher by adding a section to your
    ``dagster.yaml`` like the following:

    .. code-block:: yaml

        run_launcher:
          module: dagster_k8s.launcher
          class: K8sRunLauncher
          config:
            service_account_name: your_service_account
            job_image: my_project/dagster_image:latest
            instance_config_map: dagster-instance
            postgres_password_secret: dagster-postgresql-secret

    """

    def __init__(
        self,
        service_account_name,
        instance_config_map,
        postgres_password_secret=None,
        dagster_home=None,
        job_image=None,
        image_pull_policy=None,
        image_pull_secrets=None,
        load_incluster_config=True,
        kubeconfig_file=None,
        inst_data=None,
        job_namespace="default",
        env_config_maps=None,
        env_secrets=None,
        env_vars=None,
        k8s_client_batch_api=None,
        volume_mounts=None,
        volumes=None,
        labels=None,
        fail_pod_on_run_failure=None,
        resources=None,
        scheduler_name=None,
    ):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.job_namespace = check.str_param(job_namespace, "job_namespace")

        self.load_incluster_config = load_incluster_config
        self.kubeconfig_file = kubeconfig_file
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

        self._job_config = None
        self._job_image = check.opt_str_param(job_image, "job_image")
        self.dagster_home = check.str_param(dagster_home, "dagster_home")
        self._image_pull_policy = check.opt_str_param(
            image_pull_policy, "image_pull_policy", "IfNotPresent"
        )
        self._image_pull_secrets = check.opt_list_param(
            image_pull_secrets, "image_pull_secrets", of_type=dict
        )
        self._service_account_name = check.str_param(service_account_name, "service_account_name")
        self.instance_config_map = check.str_param(instance_config_map, "instance_config_map")
        self.postgres_password_secret = check.opt_str_param(
            postgres_password_secret, "postgres_password_secret"
        )
        self._env_config_maps = check.opt_list_param(
            env_config_maps, "env_config_maps", of_type=str
        )
        self._env_secrets = check.opt_list_param(env_secrets, "env_secrets", of_type=str)
        self._env_vars = check.opt_list_param(env_vars, "env_vars", of_type=str)
        self._volume_mounts = check.opt_list_param(volume_mounts, "volume_mounts")
        self._volumes = check.opt_list_param(volumes, "volumes")
        self._labels = check.opt_dict_param(labels, "labels", key_type=str, value_type=str)
        self._fail_pod_on_run_failure = check.opt_bool_param(
            fail_pod_on_run_failure, "fail_pod_on_run_failure"
        )
        self._resources = check.opt_dict_param(resources, "resources")
        self._scheduler_name = check.opt_str_param(scheduler_name, "scheduler_name")

        super().__init__()

    @property
    def job_image(self):
        return self._job_image

    @property
    def image_pull_policy(self) -> str:
        return self._image_pull_policy

    @property
    def image_pull_secrets(self) -> Sequence[Mapping]:
        return self._image_pull_secrets

    @property
    def service_account_name(self) -> str:
        return self._service_account_name

    @property
    def env_config_maps(self) -> Sequence[str]:
        return self._env_config_maps

    @property
    def env_secrets(self) -> Sequence[str]:
        return self._env_secrets

    @property
    def volume_mounts(self) -> Sequence:
        return self._volume_mounts

    @property
    def volumes(self) -> Sequence:
        return self._volumes

    @property
    def resources(self) -> Mapping:
        return self._resources

    @property
    def scheduler_name(self) -> str:
        return self._scheduler_name

    @property
    def env_vars(self) -> Sequence[str]:
        return self._env_vars

    @property
    def labels(self) -> Mapping[str, str]:
        return self._labels

    @property
    def fail_pod_on_run_failure(self) -> Optional[bool]:
        return self._fail_pod_on_run_failure

    @property
    def _batch_api(self):
        return self._fixed_batch_api if self._fixed_batch_api else kubernetes.client.BatchV1Api()

    @classmethod
    def config_type(cls):
        """Include all arguments required for DagsterK8sJobConfig along with additional arguments
        needed for the RunLauncher itself.
        """
        job_cfg = DagsterK8sJobConfig.config_type_run_launcher()

        run_launcher_extra_cfg = {
            "job_namespace": Field(StringSource, is_required=False, default_value="default"),
        }
        return merge_dicts(job_cfg, run_launcher_extra_cfg)

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data, **config_value)

    @property
    def inst_data(self):
        return self._inst_data

    def get_container_context_for_run(self, pipeline_run: PipelineRun) -> K8sContainerContext:
        return K8sContainerContext.create_for_run(pipeline_run, self)

    def _launch_k8s_job_with_args(self, job_name, args, run):
        container_context = self.get_container_context_for_run(run)

        pod_name = job_name

        pipeline_origin = run.pipeline_code_origin
        user_defined_k8s_config = get_user_defined_k8s_config(frozentags(run.tags))
        repository_origin = pipeline_origin.repository_origin

        job_config = container_context.get_k8s_job_config(
            job_image=repository_origin.container_image, run_launcher=self
        )

        self._instance.add_run_tags(
            run.run_id,
            {DOCKER_IMAGE_TAG: job_config.job_image},
        )

        job = construct_dagster_k8s_job(
            job_config=job_config,
            args=args,
            job_name=job_name,
            pod_name=pod_name,
            component="run_worker",
            user_defined_k8s_config=user_defined_k8s_config,
            labels={
                "dagster/job": pipeline_origin.pipeline_name,
                "dagster/run-id": run.run_id,
            },
        )

        self._instance.report_engine_event(
            "Creating Kubernetes run worker job",
            run,
            EngineEventData(
                [
                    MetadataEntry("Kubernetes Job name", value=job_name),
                    MetadataEntry("Kubernetes Namespace", value=container_context.namespace),
                    MetadataEntry("Run ID", value=run.run_id),
                ]
            ),
            cls=self.__class__,
        )

        self._batch_api.create_namespaced_job(body=job, namespace=container_context.namespace)
        self._instance.report_engine_event(
            "Kubernetes run worker job created",
            run,
            cls=self.__class__,
        )

    def launch_run(self, context: LaunchRunContext) -> None:
        run = context.pipeline_run
        job_name = get_job_name_from_run_id(run.run_id)
        pipeline_origin = check.not_none(run.pipeline_code_origin)

        args = ExecuteRunArgs(
            pipeline_origin=pipeline_origin,
            pipeline_run_id=run.run_id,
            instance_ref=self._instance.get_ref(),
            set_exit_code_on_failure=self._fail_pod_on_run_failure,
        ).get_command_args()

        self._launch_k8s_job_with_args(job_name, args, run)

    @property
    def supports_resume_run(self):
        return True

    def resume_run(self, context: ResumeRunContext) -> None:
        run = context.pipeline_run
        job_name = get_job_name_from_run_id(
            run.run_id, resume_attempt_number=context.resume_attempt_number
        )
        pipeline_origin = check.not_none(run.pipeline_code_origin)

        args = ResumeRunArgs(
            pipeline_origin=pipeline_origin,
            pipeline_run_id=run.run_id,
            instance_ref=self._instance.get_ref(),
            set_exit_code_on_failure=self._fail_pod_on_run_failure,
        ).get_command_args()

        self._launch_k8s_job_with_args(job_name, args, run)

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

        container_context = self.get_container_context_for_run(run)

        can_terminate = self.can_terminate(run_id)
        if not can_terminate:
            self._instance.report_engine_event(
                message="Unable to terminate run; can_terminate returned {}".format(can_terminate),
                pipeline_run=run,
                cls=self.__class__,
            )
            return False

        self._instance.report_run_canceling(run)

        job_name = get_job_name_from_run_id(
            run_id, resume_attempt_number=self._instance.count_resume_run_attempts(run.run_id)
        )

        try:
            termination_result = delete_job(
                job_name=job_name, namespace=container_context.namespace
            )
            if termination_result:
                self._instance.report_engine_event(
                    message="Run was terminated successfully.",
                    pipeline_run=run,
                    cls=self.__class__,
                )
            else:
                self._instance.report_engine_event(
                    message="Run was not terminated successfully; delete_job returned {}".format(
                        termination_result
                    ),
                    pipeline_run=run,
                    cls=self.__class__,
                )
            return termination_result
        except Exception:
            self._instance.report_engine_event(
                message="Run was not terminated successfully; encountered error in delete_job",
                pipeline_run=run,
                engine_event_data=EngineEventData.engine_error(
                    serializable_error_info_from_exc_info(sys.exc_info())
                ),
                cls=self.__class__,
            )

    @property
    def supports_check_run_worker_health(self):
        return True

    def check_run_worker_health(self, run: PipelineRun):
        container_context = self.get_container_context_for_run(run)

        job_name = get_job_name_from_run_id(
            run.run_id, resume_attempt_number=self._instance.count_resume_run_attempts(run.run_id)
        )
        try:
            job = self._batch_api.read_namespaced_job(
                namespace=container_context.namespace, name=job_name
            )
        except Exception:
            return CheckRunHealthResult(
                WorkerStatus.UNKNOWN, str(serializable_error_info_from_exc_info(sys.exc_info()))
            )
        if job.status.failed:
            return CheckRunHealthResult(WorkerStatus.FAILED, "K8s job failed")
        if job.status.succeeded:
            return CheckRunHealthResult(WorkerStatus.SUCCESS)
        return CheckRunHealthResult(WorkerStatus.RUNNING)
