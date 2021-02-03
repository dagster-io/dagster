import sys
import weakref

import kubernetes
from dagster import DagsterInvariantViolationError, EventMetadataEntry, Field, Noneable, check
from dagster.config.field import resolve_to_config_type
from dagster.config.validate import process_config
from dagster.core.events import EngineEventData
from dagster.core.execution.retries import Retries
from dagster.core.host_representation import (
    ExternalPipeline,
    GrpcServerRepositoryLocationHandle,
    GrpcServerRepositoryLocationOrigin,
)
from dagster.core.instance import DagsterInstance
from dagster.core.launcher import RunLauncher
from dagster.core.origin import PipelinePythonOrigin
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.serdes import ConfigurableClass, ConfigurableClassData, serialize_dagster_namedtuple
from dagster.utils import frozentags, merge_dicts
from dagster.utils.error import serializable_error_info_from_exc_info
from dagster_k8s.job import (
    DagsterK8sJobConfig,
    construct_dagster_k8s_job,
    get_job_name_from_run_id,
    get_user_defined_k8s_config,
)
from dagster_k8s.utils import delete_job

from .config import CELERY_K8S_CONFIG_KEY, celery_k8s_config


class CeleryK8sRunLauncher(RunLauncher, ConfigurableClass):
    """In contrast to the :py:class:`K8sRunLauncher`, which launches pipeline runs as single K8s
    Jobs, this run launcher is intended for use in concert with
    :py:func:`dagster_celery_k8s.celery_k8s_job_executor`.

    With this run launcher, execution is delegated to:

        1. A run coordinator Kubernetes Job, which traverses the pipeline run execution plan and
           submits steps to Celery queues for execution;
        2. The step executions which are submitted to Celery queues are picked up by Celery workers,
           and each step execution spawns a step execution Kubernetes Job. See the implementation
           defined in :py:func:`dagster_celery_k8.executor.create_k8s_job_task`.

    You may configure a Dagster instance to use this RunLauncher by adding a section to your
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

    As always when using a :py:class:`~dagster.serdes.ConfigurableClass`, the values
    under the ``config`` key of this YAML block will be passed to the constructor. The full list
    of acceptable values is given below by the constructor args.

    Args:
        instance_config_map (str): The ``name`` of an existing Volume to mount into the pod in
            order to provide a ConfigMap for the Dagster instance. This Volume should contain a
            ``dagster.yaml`` with appropriate values for run storage, event log storage, etc.
        dagster_home (str): The location of DAGSTER_HOME in the Job container; this is where the
            ``dagster.yaml`` file will be mounted from the instance ConfigMap specified above.
        postgres_password_secret (str): The name of the Kubernetes Secret where the postgres
            password can be retrieved. Will be mounted and supplied as an environment variable to
            the Job Pod.
        load_incluster_config (Optional[bool]):  Set this value if you are running the launcher
            within a k8s cluster. If ``True``, we assume the launcher is running within the target
            cluster and load config using ``kubernetes.config.load_incluster_config``. Otherwise,
            we will use the k8s config specified in ``kubeconfig_file`` (using
            ``kubernetes.config.load_kube_config``) or fall back to the default kubeconfig. Default:
            ``True``.
        kubeconfig_file (Optional[str]): The kubeconfig file from which to load config. Defaults to
            None (using the default kubeconfig).
        broker (Optional[str]): The URL of the Celery broker.
        backend (Optional[str]): The URL of the Celery backend.
        include (List[str]): List of includes for the Celery workers
        config_source: (Optional[dict]): Additional settings for the Celery app.
        retries: (Optional[dict]): Default retry configuration for Celery tasks.
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

        self._batch_api = k8s_client_batch_api or kubernetes.client.BatchV1Api()

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
        self.retries = Retries.from_config(retries)
        self._instance_ref = None

    @classmethod
    def config_type(cls):
        """Include all arguments required for DagsterK8sJobConfig along with additional arguments
        needed for the RunLauncher itself.
        """
        from dagster_celery.executor import CELERY_CONFIG

        job_cfg = DagsterK8sJobConfig.config_type_run_launcher()

        run_launcher_extra_cfg = {
            "load_incluster_config": Field(bool, is_required=False, default_value=True),
            "kubeconfig_file": Field(Noneable(str), is_required=False, default_value=None),
        }

        res = merge_dicts(job_cfg, run_launcher_extra_cfg)
        return merge_dicts(res, CELERY_CONFIG)

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data, **config_value)

    @property
    def inst_data(self):
        return self._inst_data

    @property
    def _instance(self):
        return self._instance_ref() if self._instance_ref else None

    def initialize(self, instance):
        check.inst_param(instance, "instance", DagsterInstance)
        # Store a weakref to avoid a circular reference / enable GC
        self._instance_ref = weakref.ref(instance)

    def launch_run(self, instance, run, external_pipeline):
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(run, "run", PipelineRun)
        check.inst_param(external_pipeline, "external_pipeline", ExternalPipeline)

        job_name = get_job_name_from_run_id(run.run_id)
        pod_name = job_name
        exc_config = _get_validated_celery_k8s_executor_config(run.run_config)

        job_image = None
        pipeline_origin = None
        env_vars = None

        job_image_from_executor_config = exc_config.get("job_image")

        # If the user is using user-code deployments, we grab the image from the gRPC server.
        if isinstance(
            external_pipeline.get_external_origin().external_repository_origin.repository_location_origin,
            GrpcServerRepositoryLocationOrigin,
        ):

            repository_location_handle = (
                external_pipeline.repository_handle.repository_location_handle
            )

            if not isinstance(repository_location_handle, GrpcServerRepositoryLocationHandle):
                raise DagsterInvariantViolationError(
                    "Expected RepositoryLocationHandle to be of type "
                    "GrpcServerRepositoryLocationHandle but found type {}".format(
                        type(repository_location_handle)
                    )
                )

            repository_name = external_pipeline.repository_handle.repository_name
            repository_origin = repository_location_handle.reload_repository_python_origin(
                repository_name
            )
            pipeline_origin = PipelinePythonOrigin(
                pipeline_name=external_pipeline.name, repository_origin=repository_origin
            )

            job_image = repository_origin.container_image
            env_vars = {"DAGSTER_CURRENT_IMAGE": job_image}

            if job_image_from_executor_config:
                raise DagsterInvariantViolationError(
                    "You have specified a job_image {job_image_from_executor_config} in your executor configuration, "
                    "but also {job_image} in your user-code deployment. You cannot specify a job_image "
                    "in your executor config when using user-code deployments because the job image is "
                    "pulled from the deployment. To resolve this error, remove the job_image "
                    "configuration from your executor configuration (which is a part of your run configuration)"
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
            pipeline_origin = external_pipeline.get_python_origin()

        job_config = DagsterK8sJobConfig(
            dagster_home=self.dagster_home,
            instance_config_map=self.instance_config_map,
            postgres_password_secret=self.postgres_password_secret,
            job_image=check.str_param(job_image, "job_image"),
            image_pull_policy=exc_config.get("image_pull_policy"),
            image_pull_secrets=exc_config.get("image_pull_secrets"),
            service_account_name=exc_config.get("service_account_name"),
            env_config_maps=exc_config.get("env_config_maps"),
            env_secrets=exc_config.get("env_secrets"),
        )

        user_defined_k8s_config = get_user_defined_k8s_config(frozentags(run.tags))

        from dagster.cli.api import ExecuteRunArgs

        input_json = serialize_dagster_namedtuple(
            # depends on DagsterInstance.get() returning the same instance
            # https://github.com/dagster-io/dagster/issues/2757
            ExecuteRunArgs(
                pipeline_origin=pipeline_origin,
                pipeline_run_id=run.run_id,
                instance_ref=None,
            )
        )

        job = construct_dagster_k8s_job(
            job_config,
            args=["dagster", "api", "execute_run", input_json],
            job_name=job_name,
            pod_name=pod_name,
            component="run_coordinator",
            user_defined_k8s_config=user_defined_k8s_config,
            env_vars=env_vars,
        )

        job_namespace = exc_config.get("job_namespace")

        self._batch_api.create_namespaced_job(body=job, namespace=job_namespace)
        self._instance.report_engine_event(
            "Kubernetes run_coordinator job launched",
            run,
            EngineEventData(
                [
                    EventMetadataEntry.text(job_name, "Kubernetes Job name"),
                    EventMetadataEntry.text(job_namespace, "Kubernetes Namespace"),
                    EventMetadataEntry.text(run.run_id, "Run ID"),
                ]
            ),
            cls=self.__class__,
        )
        return run

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
                message="Unable to terminate pipeline: can_terminate returned {}.".format(
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
                    message="Pipeline was terminated successfully.",
                    pipeline_run=run,
                    cls=self.__class__,
                )
            else:
                self._instance.report_engine_event(
                    message="Pipeline was not terminated successfully; delete_job returned {}".format(
                        termination_result
                    ),
                    pipeline_run=run,
                    cls=self.__class__,
                )
            return termination_result
        except Exception:  # pylint: disable=broad-except
            self._instance.report_engine_event(
                message="Pipeline was not terminated successfully; encountered error in delete_job",
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


def _get_validated_celery_k8s_executor_config(run_config):
    check.dict_param(run_config, "run_config")

    executor_config = run_config.get("execution", {})
    if not CELERY_K8S_CONFIG_KEY in executor_config:
        raise DagsterInvariantViolationError(
            "{config_key} execution configuration must be present in the run config to use the CeleryK8sRunLauncher. "
            "Note: You may also be seeing this error because you are using the configured API. "
            "Using configured with the {config_key} executor is not supported at this time, "
            "and all executor config must be directly in the run config without using configured.".format(
                config_key=CELERY_K8S_CONFIG_KEY,
            ),
        )

    execution_config_schema = resolve_to_config_type(celery_k8s_config())
    execution_run_config = run_config["execution"][CELERY_K8S_CONFIG_KEY].get("config", {})
    res = process_config(execution_config_schema, execution_run_config)

    check.invariant(
        res.success, "Incorrect {} execution schema provided".format(CELERY_K8S_CONFIG_KEY)
    )

    return res.value
