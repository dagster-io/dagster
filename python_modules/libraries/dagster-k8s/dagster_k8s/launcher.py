import logging
import sys
from collections.abc import Mapping, Sequence
from typing import Any

from dagster import (
    Field,
    StringSource,
    _check as check,
)
from dagster._cli.api import ExecuteRunArgs
from dagster._core.events import EngineEventData
from dagster._core.launcher import LaunchRunContext, ResumeRunContext, RunLauncher
from dagster._core.launcher.base import (
    BackfillWorkerCreationStatus,
    BackfillWorkerExitStatus,
    CheckRunHealthResult,
    WorkerStatus,
)
from dagster._core.storage.dagster_run import DagsterRun, DagsterRunStatus
from dagster._core.storage.runs.base import (
    BackfillWorkerLaunch,
    ChildWorkerTarget,
    K8sPodWorkerTarget,
    K8sWorkerTarget,
)
from dagster._core.storage.tags import BACKFILL_STOP_PROTOCOL_VERSION, DOCKER_IMAGE_TAG
from dagster._grpc.types import ResumeRunArgs
from dagster._serdes import ConfigurableClass, ConfigurableClassData
from dagster._utils.error import serializable_error_info_from_exc_info
from kubernetes.client import (
    AdmissionregistrationV1Api,
    V1DeleteOptions,
    V1ObjectMeta,
    V1Preconditions,
)
from kubernetes.client.rest import ApiException

from dagster_k8s.backfill_admission import (
    ADMISSION_ID_ANNOTATION,
    ADMISSION_ROUTE_LABEL,
    ADMISSION_WEBHOOK_NAME,
    DISPATCH_ID_ANNOTATION,
    POD_FINALIZER,
    PROTOCOL_LABEL,
    require_backfill_worker_policy,
    stamp_backfill_job,
)
from dagster_k8s.backfill_worker import PodSnapshot, WebhookConfiguration
from dagster_k8s.client import DagsterKubernetesClient
from dagster_k8s.container_context import K8sContainerContext
from dagster_k8s.job import DagsterK8sJobConfig, construct_dagster_k8s_job, get_job_name_from_run_id
from dagster_k8s.utils import get_deployment_id_label, load_kubernetes_config


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
        k8s_api_ssl_ca_cert_file=None,
        inst_data: ConfigurableClassData | None = None,
        job_namespace="default",
        env_config_maps=None,
        env_secrets=None,
        env_vars=None,
        k8s_client_batch_api=None,
        k8s_client_core_api=None,
        volume_mounts=None,
        volumes=None,
        labels=None,
        fail_pod_on_run_failure=None,
        resources=None,
        scheduler_name=None,
        security_context=None,
        run_k8s_config=None,
        only_allow_user_defined_k8s_config_fields=None,
        only_allow_user_defined_env_vars=None,
        backfill_worker_admission_webhook_name=ADMISSION_WEBHOOK_NAME,
    ):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)
        self.backfill_worker_admission_webhook_name = check.str_param(
            backfill_worker_admission_webhook_name, "backfill_worker_admission_webhook_name"
        )
        self.job_namespace = check.str_param(job_namespace, "job_namespace")

        self.load_incluster_config = load_incluster_config
        self.kubeconfig_file = check.opt_str_param(kubeconfig_file, "kubeconfig_file")
        load_kubernetes_config(
            load_incluster_config=load_incluster_config,
            kubeconfig_file=kubeconfig_file,
            k8s_api_ssl_ca_cert_file=k8s_api_ssl_ca_cert_file,
        )

        self._api_client = DagsterKubernetesClient.production_client(
            core_api_override=k8s_client_core_api,
            batch_api_override=k8s_client_batch_api,
        )

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
        self._labels: Mapping[str, str] = check.opt_mapping_param(
            labels, "labels", key_type=str, value_type=str
        )
        self._fail_pod_on_run_failure = check.opt_bool_param(
            fail_pod_on_run_failure, "fail_pod_on_run_failure"
        )
        self._resources: Mapping[str, Any] = check.opt_mapping_param(resources, "resources")
        self._scheduler_name = check.opt_str_param(scheduler_name, "scheduler_name")
        self._security_context = check.opt_dict_param(security_context, "security_context")
        self._run_k8s_config = check.opt_dict_param(run_k8s_config, "run_k8s_config")

        self._only_allow_user_defined_k8s_config_fields = only_allow_user_defined_k8s_config_fields
        self._only_allow_user_defined_env_vars = only_allow_user_defined_env_vars
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
    def scheduler_name(self) -> str | None:
        return self._scheduler_name

    @property
    def security_context(self) -> Mapping[str, Any]:
        return self._security_context

    @property
    def env_vars(self) -> Sequence[str]:
        return self._env_vars

    @property
    def labels(self) -> Mapping[str, str]:
        return self._labels

    @property
    def run_k8s_config(self) -> Mapping[str, str]:
        return self._run_k8s_config

    @property
    def fail_pod_on_run_failure(self) -> bool | None:
        return self._fail_pod_on_run_failure

    @property
    def only_allow_user_defined_k8s_config_fields(self) -> Mapping[str, Any] | None:
        return self._only_allow_user_defined_k8s_config_fields

    @property
    def only_allow_user_defined_env_vars(self) -> Sequence[str] | None:
        return self._only_allow_user_defined_env_vars

    @classmethod
    def config_type(cls):
        """Include all arguments required for DagsterK8sJobConfig along with additional arguments
        needed for the RunLauncher itself.
        """
        return {
            **DagsterK8sJobConfig.config_type_run_launcher(),
            "backfill_worker_admission_webhook_name": Field(
                StringSource, default_value=ADMISSION_WEBHOOK_NAME, is_required=False
            ),
        }

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data, **config_value)

    @property
    def inst_data(self) -> ConfigurableClassData | None:
        return self._inst_data

    def get_container_context_for_run(self, dagster_run: DagsterRun) -> K8sContainerContext:
        return K8sContainerContext.create_for_run(dagster_run, self, include_run_tags=True)

    def _report_run_worker_creating(self, run: DagsterRun, job_name: str, namespace: str) -> None:
        self._instance.report_engine_event(
            "Creating Kubernetes run worker job",
            run,
            EngineEventData(
                {
                    "Kubernetes Job name": job_name,
                    "Kubernetes Namespace": namespace,
                    "Run ID": run.run_id,
                }
            ),
            cls=self.__class__,
        )

    def _report_run_worker_created(self, run: DagsterRun) -> None:
        self._instance.report_engine_event(
            "Kubernetes run worker job created",
            run,
            cls=self.__class__,
        )

    def _report_run_terminated(self, run: DagsterRun) -> None:
        self._instance.report_engine_event(
            message="Run was terminated successfully.",
            dagster_run=run,
            cls=self.__class__,
        )

    def _report_run_termination_failed(self, run: DagsterRun, result: object) -> None:
        self._instance.report_engine_event(
            message=f"Run was not terminated successfully; delete_job returned {result}",
            dagster_run=run,
            cls=self.__class__,
        )

    def _report_run_termination_error(self, run: DagsterRun) -> None:
        self._instance.report_engine_event(
            message="Run was not terminated successfully; encountered error in delete_job",
            dagster_run=run,
            engine_event_data=EngineEventData.engine_error(
                serializable_error_info_from_exc_info(sys.exc_info())
            ),
            cls=self.__class__,
        )

    def _launch_k8s_job_with_args(
        self, job_name: str, args: Sequence[str] | None, run: DagsterRun
    ) -> None:
        container_context = self.get_container_context_for_run(run)

        pod_name = job_name

        job_origin = check.not_none(run.job_code_origin)
        user_defined_k8s_config = container_context.run_k8s_config
        repository_origin = job_origin.repository_origin

        job_config = container_context.get_k8s_job_config(
            job_image=repository_origin.container_image, run_launcher=self
        )

        labels = {
            "dagster/job": job_origin.job_name,
            "dagster/run-id": run.run_id,
        }
        deployment_name_env_var = get_deployment_id_label(user_defined_k8s_config)
        if deployment_name_env_var:
            labels["dagster/deployment-name"] = deployment_name_env_var
        if run.remote_job_origin:
            labels["dagster/code-location"] = (
                run.remote_job_origin.repository_origin.code_location_origin.location_name
            )

        job = construct_dagster_k8s_job(
            job_config=job_config,
            args=args,
            job_name=job_name,
            pod_name=pod_name,
            component="run_worker",
            user_defined_k8s_config=user_defined_k8s_config,
            labels=labels,
            env_vars=[
                {
                    "name": "DAGSTER_RUN_JOB_NAME",
                    "value": job_origin.job_name,
                },
            ],
        )
        # These labels identify durable dispatch targets. Custom metadata must not replace
        # them, otherwise a detached pod could disappear from the exit-proof inventory.
        from dagster._core.execution.backfill import run_uses_stop_protocol

        if run_uses_stop_protocol(self._instance, run):
            stamp_backfill_job(job, run.run_id, "run", self.backfill_worker_admission_webhook_name)

        # Set docker/image tag here, as it can also be provided by `user_defined_k8s_config`.
        self._instance.add_run_tags(
            run.run_id,
            {DOCKER_IMAGE_TAG: job.spec.template.spec.containers[0].image},
        )

        namespace = check.not_none(container_context.namespace)

        self._report_run_worker_creating(run, job_name, namespace)

        from dagster._core.execution.backfill import run_uses_stop_protocol

        if run_uses_stop_protocol(self._instance, run):
            self._api_client.create_namespaced_job_once(body=job, namespace=namespace)
        else:
            self._api_client.create_namespaced_job_with_retries(body=job, namespace=namespace)
        self._report_run_worker_created(run)

    def launch_run(self, context: LaunchRunContext) -> None:
        run = context.dagster_run
        job_name = get_job_name_from_run_id(run.run_id)
        job_origin = check.not_none(run.job_code_origin)

        args = ExecuteRunArgs(
            job_origin=job_origin,
            run_id=run.run_id,
            instance_ref=self._instance.get_ref(),
            set_exit_code_on_failure=self._fail_pod_on_run_failure,
        ).get_command_args()

        self._launch_k8s_job_with_args(job_name, args, run)

    def get_backfill_worker_target(self, run: DagsterRun) -> K8sWorkerTarget:
        self.require_backfill_worker_admission()
        context = self.get_container_context_for_run(run)
        require_backfill_worker_policy(
            context.run_k8s_config.pod_spec_config, context.run_k8s_config.container_config
        )
        return K8sWorkerTarget(
            job_name=get_job_name_from_run_id(run.run_id),
            namespace=check.not_none(context.namespace),
            admission_webhook_name=self.backfill_worker_admission_webhook_name,
        )

    def require_backfill_worker_admission(self) -> None:
        api = AdmissionregistrationV1Api(api_client=self._api_client.batch_api.api_client)
        configuration = api.read_mutating_webhook_configuration(
            self.backfill_worker_admission_webhook_name
        )
        data = api.api_client.sanitize_for_serialization(configuration)
        WebhookConfiguration.model_validate(data).require_binding(
            self.backfill_worker_admission_webhook_name
        )

    def request_backfill_worker_stop(self, run: DagsterRun, launch: BackfillWorkerLaunch) -> None:
        target = launch.target
        if isinstance(target, ChildWorkerTarget) and isinstance(
            target.resource, K8sPodWorkerTarget
        ):
            pod = self._read_backfill_pod(launch)
            if pod is not None:
                self._api_client.core_api.delete_namespaced_pod(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    body=V1DeleteOptions(preconditions=V1Preconditions(uid=pod.metadata.uid)),
                )
            return
        if not isinstance(target, K8sWorkerTarget):
            return
        try:
            job = self._api_client.batch_api.read_namespaced_job(
                name=target.job_name, namespace=target.namespace
            )
        except ApiException as error:
            if error.status != 404:
                raise
        else:
            check.invariant(
                self._matches_backfill_worker_labels(job.metadata, target, launch.run_id)
                and job.metadata.name == target.job_name
                and job.metadata.uid,
                "Kubernetes Job identity does not match the durable worker target.",
            )
            try:
                self._api_client.batch_api.delete_namespaced_job(
                    name=target.job_name,
                    namespace=target.namespace,
                    body=V1DeleteOptions(
                        propagation_policy="Foreground",
                        preconditions=V1Preconditions(uid=job.metadata.uid),
                    ),
                )
            except ApiException as error:
                if error.status != 404:
                    raise
        pods = self._api_client.core_api.list_namespaced_pod(
            namespace=target.namespace, label_selector=f"dagster/worker-job={target.job_name}"
        )
        for pod in pods.items:
            check.invariant(
                self._matches_backfill_worker_labels(pod.metadata, target, launch.run_id)
                and pod.metadata.uid,
                "Kubernetes Pod identity does not match the durable worker target.",
            )
            try:
                self._api_client.core_api.delete_namespaced_pod(
                    name=pod.metadata.name,
                    namespace=target.namespace,
                    body=V1DeleteOptions(preconditions=V1Preconditions(uid=pod.metadata.uid)),
                )
            except ApiException as error:
                if error.status != 404:
                    raise

    @staticmethod
    def _matches_backfill_worker_labels(
        metadata: V1ObjectMeta | None, target: K8sWorkerTarget, run_id: str
    ) -> bool:
        return bool(
            metadata is not None
            and metadata.namespace == target.namespace
            and (metadata.labels or {}).get("dagster/run-id") == run_id
            and (metadata.labels or {}).get("dagster/worker-job") == target.job_name
            and (metadata.labels or {}).get(ADMISSION_ROUTE_LABEL) == target.admission_webhook_name
            and (metadata.labels or {}).get(PROTOCOL_LABEL) == BACKFILL_STOP_PROTOCOL_VERSION
        )

    def get_backfill_worker_exit_status(
        self, run: DagsterRun, launch: BackfillWorkerLaunch
    ) -> BackfillWorkerExitStatus:
        target = launch.target
        if isinstance(target, ChildWorkerTarget) and isinstance(
            target.resource, K8sPodWorkerTarget
        ):
            try:
                pod = self._read_backfill_pod(launch)
                if pod is None:
                    return (
                        BackfillWorkerExitStatus.EXITED
                        if launch.acknowledged
                        else BackfillWorkerExitStatus.UNKNOWN
                    )
                # BindingREST checks deletionTimestamp in the same storage update as nodeName.
                # A deleting, unassigned Pod therefore cannot start executing later.
                # https://github.com/kubernetes/kubernetes/blob/v1.35.0/pkg/registry/core/pod/storage/storage.go
                if not pod.spec.node_name and pod.metadata.deletion_timestamp is not None:
                    return BackfillWorkerExitStatus.EXITED
                if pod.status.phase in ("Succeeded", "Failed") and pod.all_containers_terminated:
                    return BackfillWorkerExitStatus.EXITED
                return BackfillWorkerExitStatus.RUNNING
            except Exception:
                return BackfillWorkerExitStatus.UNKNOWN
        if not isinstance(target, K8sWorkerTarget):
            return BackfillWorkerExitStatus.UNKNOWN
        try:
            job = None
            try:
                job = self._api_client.batch_api.read_namespaced_job(
                    name=target.job_name, namespace=target.namespace
                )
            except ApiException as error:
                if error.status != 404:
                    raise
            if job is not None:
                metadata = job.metadata
                if (
                    not self._matches_backfill_worker_labels(metadata, target, launch.run_id)
                    or metadata.name != target.job_name
                    or not metadata.uid
                ):
                    return BackfillWorkerExitStatus.UNKNOWN
                # Kubernetes >=1.31 only publishes these terminal Job conditions after all
                # Job pods terminate. FailureTarget and SuccessCriteriaMet occur earlier.
                # https://kubernetes.io/docs/concepts/workloads/controllers/job/#terminal-job-conditions
                terminal = job.status is not None and any(
                    condition.type in ("Complete", "Failed") and condition.status == "True"
                    for condition in (job.status.conditions or [])
                )
                if not terminal:
                    return BackfillWorkerExitStatus.RUNNING
            pods = self._api_client.core_api.list_namespaced_pod(
                namespace=target.namespace, label_selector=f"dagster/worker-job={target.job_name}"
            )
            for pod in pods.items:
                metadata = pod.metadata
                if not self._matches_backfill_worker_labels(metadata, target, launch.run_id):
                    return BackfillWorkerExitStatus.UNKNOWN
                if job is not None and not any(
                    reference.kind == "Job"
                    and reference.name == target.job_name
                    and reference.uid == job.metadata.uid
                    for reference in (metadata.owner_references or [])
                ):
                    return BackfillWorkerExitStatus.UNKNOWN
            if job is None:
                return (
                    BackfillWorkerExitStatus.RUNNING
                    if pods.items
                    else BackfillWorkerExitStatus.EXITED
                )
            for pod in pods.items:
                if pod.status is None or pod.status.phase not in ("Succeeded", "Failed"):
                    return BackfillWorkerExitStatus.RUNNING
                statuses = [
                    *(pod.status.container_statuses or []),
                    *(pod.status.init_container_statuses or []),
                    *(pod.status.ephemeral_container_statuses or []),
                ]
                if any(
                    status.state is None or status.state.terminated is None for status in statuses
                ):
                    return BackfillWorkerExitStatus.RUNNING
            return BackfillWorkerExitStatus.EXITED
        except Exception:
            return BackfillWorkerExitStatus.UNKNOWN

    def _read_backfill_pod(self, launch: BackfillWorkerLaunch) -> PodSnapshot | None:
        target = check.inst(launch.target, ChildWorkerTarget)
        resource = check.inst(target.resource, K8sPodWorkerTarget)
        api = self._api_client.core_api
        try:
            result = api.read_namespaced_pod(resource.pod_name, resource.namespace)
        except ApiException as error:
            if error.status == 404:
                return None
            raise
        pod = PodSnapshot.model_validate(api.api_client.sanitize_for_serialization(result))
        metadata = pod.metadata
        check.invariant(
            metadata.name == resource.pod_name
            and metadata.namespace == resource.namespace
            and metadata.labels.get("dagster/run-id") == launch.run_id
            and metadata.labels.get("dagster/worker-job") == resource.job_name
            and metadata.labels.get(ADMISSION_ROUTE_LABEL)
            == self.backfill_worker_admission_webhook_name
            and metadata.labels.get(PROTOCOL_LABEL) == BACKFILL_STOP_PROTOCOL_VERSION
            and metadata.annotations.get(ADMISSION_ID_ANNOTATION) == resource.admission_id
            and metadata.annotations.get(DISPATCH_ID_ANNOTATION) == target.parent_worker_id
            and any(
                owner.kind == "Job"
                and owner.controller
                and owner.name == resource.job_name
                and owner.uid == resource.job_uid
                for owner in metadata.owners
            ),
            "Kubernetes Pod identity does not match the durable admission target.",
        )
        return pod

    def get_backfill_worker_creation_status(
        self, run: DagsterRun, launch: BackfillWorkerLaunch
    ) -> BackfillWorkerCreationStatus:
        if not isinstance(launch.target, ChildWorkerTarget) or not isinstance(
            launch.target.resource, K8sPodWorkerTarget
        ):
            return BackfillWorkerCreationStatus.UNKNOWN
        try:
            pod = self._read_backfill_pod(launch)
            if pod is not None and POD_FINALIZER in pod.metadata.finalizers:
                return BackfillWorkerCreationStatus.CREATED
        except Exception:
            pass
        return BackfillWorkerCreationStatus.UNKNOWN

    def cleanup_backfill_worker_launch(self, run: DagsterRun, launch: BackfillWorkerLaunch) -> None:
        if not isinstance(launch.target, ChildWorkerTarget) or not isinstance(
            launch.target.resource, K8sPodWorkerTarget
        ):
            return
        pod = self._read_backfill_pod(launch)
        if pod is None or POD_FINALIZER not in pod.metadata.finalizers:
            return
        self._api_client.core_api.patch_namespaced_pod(
            name=pod.metadata.name,
            namespace=pod.metadata.namespace,
            body=[
                {"op": "test", "path": "/metadata/uid", "value": pod.metadata.uid},
                {
                    "op": "test",
                    "path": "/metadata/resourceVersion",
                    "value": pod.metadata.resource_version,
                },
                {
                    "op": "replace",
                    "path": "/metadata/finalizers",
                    "value": [item for item in pod.metadata.finalizers if item != POD_FINALIZER],
                },
            ],
        )

    @property
    def supports_resume_run(self):
        return True

    def resume_run(self, context: ResumeRunContext) -> None:
        run = context.dagster_run
        job_name = get_job_name_from_run_id(
            run.run_id, resume_attempt_number=context.resume_attempt_number
        )
        job_origin = check.not_none(run.job_code_origin)

        args = ResumeRunArgs(
            job_origin=job_origin,
            run_id=run.run_id,
            instance_ref=self._instance.get_ref(),
            set_exit_code_on_failure=self._fail_pod_on_run_failure,
        ).get_command_args()

        self._launch_k8s_job_with_args(job_name, args, run)

    def _get_resume_attempt_number(self, run: DagsterRun) -> int | None:
        if not self.supports_run_worker_crash_recovery:
            return None
        return self._instance.count_resume_run_attempts(run.run_id)

    def terminate(self, run_id):
        check.str_param(run_id, "run_id")
        run = self._instance.get_run_by_id(run_id)

        if not run or run.is_finished:
            return False

        self._instance.report_run_canceling(run)

        container_context = self.get_container_context_for_run(run)

        job_name = get_job_name_from_run_id(
            run_id, resume_attempt_number=self._get_resume_attempt_number(run)
        )

        try:
            termination_result = self._api_client.delete_job(
                job_name=job_name, namespace=container_context.namespace
            )
            if termination_result:
                self._report_run_terminated(run)
            else:
                self._report_run_termination_failed(run, termination_result)
            return termination_result
        except Exception:
            self._report_run_termination_error(run)

    @property
    def supports_check_run_worker_health(self):
        return True

    @property
    def supports_run_worker_crash_recovery(self):
        return True

    def get_run_worker_debug_info(
        self, run: DagsterRun, include_container_logs: bool | None = True
    ) -> str | None:
        container_context = self.get_container_context_for_run(run)

        job_name = get_job_name_from_run_id(
            run.run_id, resume_attempt_number=self._get_resume_attempt_number(run)
        )
        namespace = container_context.namespace
        pod_names = self._api_client.get_pod_names_in_job(job_name, namespace=namespace)
        full_msg = ""
        try:
            pod_debug_info = [
                self._api_client.get_pod_debug_info(
                    pod_name, namespace, include_container_logs=include_container_logs
                )
                for pod_name in pod_names
            ]
            full_msg = "\n".join(pod_debug_info)
        except Exception:
            logging.exception(
                f"Error trying to get debug information for failed k8s job {job_name}"
            )
        if pod_names:
            full_msg = (
                full_msg
                + "\nFor more information about the failure, try running `kubectl describe pod"
                f" {pod_names[0]}`, `kubectl logs {pod_names[0]}`, or `kubectl describe job"
                f" {job_name}` in your cluster."
            )

        else:
            job_debug_info = self._api_client.get_job_debug_info(job_name, namespace=namespace)
            full_msg = (
                full_msg
                + "\n\n"
                + job_debug_info
                + "\n\nFor more information about the failure, try running `kubectl describe job"
                f" {job_name}` in your cluster."
            )

        return full_msg

    def check_run_worker_health(self, run: DagsterRun):
        container_context = self.get_container_context_for_run(run)

        job_name = get_job_name_from_run_id(
            run.run_id, resume_attempt_number=self._get_resume_attempt_number(run)
        )
        try:
            status = self._api_client.get_job_status(
                namespace=container_context.namespace,
                job_name=job_name,
            )
        except Exception:
            return CheckRunHealthResult(
                WorkerStatus.UNKNOWN, str(serializable_error_info_from_exc_info(sys.exc_info()))
            )

        if not status:
            return CheckRunHealthResult(WorkerStatus.UNKNOWN, f"Job {job_name} could not be found")

        inactive_job_with_finished_pods = bool(
            (not status.active) and (status.failed or status.succeeded)
        )

        # If the run is in a non-terminal (and non-STARTING) state but the k8s job is not active,
        # something went wrong
        if (
            run.status in (DagsterRunStatus.STARTED, DagsterRunStatus.CANCELING)
            and inactive_job_with_finished_pods
        ):
            return CheckRunHealthResult(
                WorkerStatus.FAILED, "Run has not completed but K8s job has no active pods"
            )

        if status.succeeded:
            return CheckRunHealthResult(WorkerStatus.SUCCESS)
        if status.failed and not status.active:
            return CheckRunHealthResult(WorkerStatus.FAILED, "K8s job failed")
        return CheckRunHealthResult(WorkerStatus.RUNNING)
