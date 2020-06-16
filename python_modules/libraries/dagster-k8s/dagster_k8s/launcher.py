import kubernetes

from dagster import EventMetadataEntry, Field, Noneable, StringSource, check, seven
from dagster.config.field import resolve_to_config_type
from dagster.config.validate import process_config
from dagster.core.events import EngineEventData
from dagster.core.execution.retries import Retries
from dagster.core.host_representation import ExternalPipeline
from dagster.core.instance import DagsterInstance
from dagster.core.launcher import RunLauncher
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.serdes import ConfigurableClass, ConfigurableClassData
from dagster.utils import merge_dicts

from .job import DagsterK8sJobConfig, construct_dagster_graphql_k8s_job
from .utils import DagsterK8sError


class K8sRunLauncher(RunLauncher, ConfigurableClass):
    '''RunLauncher that starts a Kubernetes Job for each pipeline run.

    Encapsulates each pipeline run in a separate, isolated invocation of ``dagster-graphql``.

    You may configure a Dagster instance to use this RunLauncher by adding a section to your
    ``dagster.yaml`` like the following:

    .. code-block:: yaml

        run_launcher:
            module: dagster_k8s.launcher
            class: K8sRunLauncher
            config:
                service_account_name: pipeline_run_service_account
                job_image: my_project/dagster_image:latest
                instance_config_map: dagster-instance
                postgres_password_secret: dagster-postgresql-secret

    As always when using a :py:class:`~dagster.serdes.ConfigurableClass`, the values
    under the ``config`` key of this YAML block will be passed to the constructor. The full list
    of acceptable values is given below by the constructor args.

    Args:
        service_account_name (str): The name of the Kubernetes service account under which to run
            the Job.
        job_image (str): The ``name`` of the image to use for the Job's Dagster container. This
            image will be run with the command
            ``dagster-graphql -p startPipelineExecution -v {executionParams}``.
        instance_config_map (str): The ``name`` of an existing Volume to mount into the pod in
            order to provide a ConfigMap for the Dagster instance. This Volume should contain a
            ``dagster.yaml`` with appropriate values for run storage, event log storage, etc.
        postgres_password_secret (str): The name of the Kubernetes Secret where the postgres
            password can be retrieved. Will be mounted and supplied as an environment variable to
            the Job Pod.
        dagster_home (str): The location of DAGSTER_HOME in the Job container; this is where the
            ``dagster.yaml`` file will be mounted from the instance ConfigMap specified above.
        load_incluster_config (Optional[bool]):  Set this value if you are running the launcher
            within a k8s cluster. If ``True``, we assume the launcher is running within the target
            cluster and load config using ``kubernetes.config.load_incluster_config``. Otherwise,
            we will use the k8s config specified in ``kubeconfig_file`` (using
            ``kubernetes.config.load_kube_config``) or fall back to the default kubeconfig. Default:
            ``True``.
        kubeconfig_file (Optional[str]): The kubeconfig file from which to load config. Defaults to
            None (using the default kubeconfig).
        image_pull_secrets (Optional[List[Dict[str, str]]]): Optionally, a list of dicts, each of
            which corresponds to a Kubernetes ``LocalObjectReference`` (e.g.,
            ``{'name': 'myRegistryName'}``). This allows you to specify the ```imagePullSecrets`` on
            a pod basis. Typically, these will be provided through the service account, when needed,
            and you will not need to pass this argument.
            See:
            https://kubernetes.io/docs/concepts/containers/images/#specifying-imagepullsecrets-on-a-pod
            and https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.17/#podspec-v1-core.
        image_pull_policy (Optional[str]): Allows the image pull policy to be overridden, e.g. to
            facilitate local testing with `kind <https://kind.sigs.k8s.io/>`_. Default:
            ``"Always"``. See: https://kubernetes.io/docs/concepts/containers/images/#updating-images.
        job_namespace (Optional[str]): The namespace into which to launch new jobs. Note that any
            other Kubernetes resources the Job requires (such as the service account) must be
            present in this namespace. Default: ``"default"``
        env_config_maps (Optional[List[str]]): A list of custom ConfigMapEnvSource names from which to
            draw environment variables (using ``envFrom``) for the Job. Default: ``[]``. See:
        https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/#define-an-environment-variable-for-a-container
        env_secrets (Optional[List[str]]): A list of custom Secret names from which to
            draw environment variables (using ``envFrom``) for the Job. Default: ``[]``. See:
        https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables
    '''

    def __init__(
        self,
        service_account_name,
        job_image,
        instance_config_map,
        postgres_password_secret,
        dagster_home,
        image_pull_policy='Always',
        image_pull_secrets=None,
        load_incluster_config=True,
        kubeconfig_file=None,
        inst_data=None,
        job_namespace='default',
        env_config_maps=None,
        env_secrets=None,
    ):
        self._inst_data = check.opt_inst_param(inst_data, 'inst_data', ConfigurableClassData)
        self.job_namespace = check.str_param(job_namespace, 'job_namespace')

        if load_incluster_config:
            check.invariant(
                kubeconfig_file is None,
                '`kubeconfig_file` is set but `load_incluster_config` is True.',
            )
            kubernetes.config.load_incluster_config()
        else:
            check.opt_str_param(kubeconfig_file, 'kubeconfig_file')
            kubernetes.config.load_kube_config(kubeconfig_file)

        self.job_config = DagsterK8sJobConfig(
            job_image=check.str_param(job_image, 'job_image'),
            dagster_home=check.str_param(dagster_home, 'dagster_home'),
            image_pull_policy=check.str_param(image_pull_policy, 'image_pull_policy'),
            image_pull_secrets=check.opt_list_param(
                image_pull_secrets, 'image_pull_secrets', of_type=dict
            ),
            service_account_name=check.str_param(service_account_name, 'service_account_name'),
            instance_config_map=check.str_param(instance_config_map, 'instance_config_map'),
            postgres_password_secret=check.str_param(
                postgres_password_secret, 'postgres_password_secret'
            ),
            env_config_maps=check.opt_list_param(env_config_maps, 'env_config_maps', of_type=str),
            env_secrets=check.opt_list_param(env_secrets, 'env_secrets', of_type=str),
        )

    @classmethod
    def config_type(cls):
        '''Include all arguments required for DagsterK8sJobConfig along with additional arguments
        needed for the RunLauncher itself.
        '''
        job_cfg = DagsterK8sJobConfig.config_type()

        run_launcher_extra_cfg = {
            'job_namespace': StringSource,
            'load_incluster_config': Field(bool, is_required=False, default_value=True),
            'kubeconfig_file': Field(Noneable(str), is_required=False, default_value=None),
        }
        return merge_dicts(job_cfg, run_launcher_extra_cfg)

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data, **config_value)

    @property
    def inst_data(self):
        return self._inst_data

    def launch_run(self, instance, run, external_pipeline):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(run, 'run', PipelineRun)
        check.inst_param(external_pipeline, 'external_pipeline', ExternalPipeline)

        job_name = 'dagster-run-{}'.format(run.run_id)
        pod_name = job_name

        job = construct_dagster_graphql_k8s_job(
            self.job_config,
            args=[
                '-p',
                'executeRunInProcess',
                '-v',
                seven.json.dumps(
                    {
                        'runId': run.run_id,
                        'repositoryName': external_pipeline.handle.repository_name,
                        'repositoryLocationName': external_pipeline.handle.location_name,
                    }
                ),
            ],
            job_name=job_name,
            pod_name=pod_name,
            component='runmaster',
        )

        api = kubernetes.client.BatchV1Api()
        api.create_namespaced_job(body=job, namespace=self.job_namespace)

        instance.report_engine_event(
            'Kubernetes runmaster job launched',
            run,
            EngineEventData(
                [
                    EventMetadataEntry.text(job_name, 'Kubernetes Job name'),
                    EventMetadataEntry.text(pod_name, 'Kubernetes Pod name'),
                    EventMetadataEntry.text(self.job_namespace, 'Kubernetes Namespace'),
                    EventMetadataEntry.text(run.run_id, 'Run ID'),
                ]
            ),
            cls=K8sRunLauncher,
        )
        return run

    def can_terminate(self, run_id):
        check.str_param(run_id, 'run_id')
        return False

    def terminate(self, run_id):
        check.str_param(run_id, 'run_id')
        check.not_implemented('Termination not yet implemented')


class CeleryK8sRunLauncher(RunLauncher, ConfigurableClass):
    '''In contrast to the :py:class:`K8sRunLauncher`, which launches pipeline runs as single K8s
    Jobs, this run launcher is intended for use in concert with
    :py:func:`dagster_celery.executor_k8s.celery_k8s_job_executor`.

    With this run launcher, execution is delegated to:

        1. A run master Kubernetes Job, which traverses the pipeline run execution plan and submits
           steps to Celery queues for execution;
        2. The step executions which are submitted to Celery queues are picked up by Celery workers,
           and each step execution spawns a step execution Kubernetes Job. See the implementation
           defined in :py:func:`dagster_celery.tasks.create_k8s_job_task`.

    You may configure a Dagster instance to use this RunLauncher by adding a section to your
    ``dagster.yaml`` like the following:

    .. code-block:: yaml

        run_launcher:
          module: dagster_k8s.launcher
          class: CeleryK8sRunLauncher
          config:
            instance_config_map: "dagster-k8s-instance-config-map"
            dagter_home: "/some/path"
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
    '''

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
    ):
        self._inst_data = check.opt_inst_param(inst_data, 'inst_data', ConfigurableClassData)

        if load_incluster_config:
            check.invariant(
                kubeconfig_file is None,
                '`kubeconfig_file` is set but `load_incluster_config` is True.',
            )
            kubernetes.config.load_incluster_config()
        else:
            check.opt_str_param(kubeconfig_file, 'kubeconfig_file')
            kubernetes.config.load_kube_config(kubeconfig_file)

        self.instance_config_map = check.str_param(instance_config_map, 'instance_config_map')
        self.dagster_home = check.str_param(dagster_home, 'dagster_home')
        self.postgres_password_secret = check.str_param(
            postgres_password_secret, 'postgres_password_secret'
        )
        self.broker = check.opt_str_param(broker, 'broker')
        self.backend = check.opt_str_param(backend, 'backend')
        self.include = check.opt_list_param(include, 'include')
        self.config_source = check.opt_dict_param(config_source, 'config_source')

        retries = check.opt_dict_param(retries, 'retries') or {'enabled': {}}
        self.retries = Retries.from_config(retries)

    @classmethod
    def config_type(cls):
        '''Include all arguments required for DagsterK8sJobConfig along with additional arguments
        needed for the RunLauncher itself.
        '''
        from dagster_celery.executor import CELERY_CONFIG

        job_cfg = DagsterK8sJobConfig.config_type_run_launcher()

        run_launcher_extra_cfg = {
            'load_incluster_config': Field(bool, is_required=False, default_value=True),
            'kubeconfig_file': Field(Noneable(str), is_required=False, default_value=None),
        }

        res = merge_dicts(job_cfg, run_launcher_extra_cfg)
        return merge_dicts(res, CELERY_CONFIG)

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data, **config_value)

    @property
    def inst_data(self):
        return self._inst_data

    def launch_run(self, instance, run, external_pipeline):
        check.inst_param(instance, 'instance', DagsterInstance)
        check.inst_param(run, 'run', PipelineRun)

        job_name = 'dagster-run-{}'.format(run.run_id)
        pod_name = job_name

        exc_config = _get_validated_celery_k8s_executor_config(run.run_config)

        job_config = DagsterK8sJobConfig(
            dagster_home=self.dagster_home,
            instance_config_map=self.instance_config_map,
            postgres_password_secret=self.postgres_password_secret,
            job_image=exc_config.get('job_image'),
            image_pull_policy=exc_config.get('image_pull_policy'),
            image_pull_secrets=exc_config.get('image_pull_secrets'),
            service_account_name=exc_config.get('service_account_name'),
            env_config_maps=exc_config.get('env_config_maps'),
            env_secrets=exc_config.get('env_secrets'),
        )

        job = construct_dagster_graphql_k8s_job(
            job_config,
            args=[
                '-p',
                'executeRunInProcess',
                '-v',
                seven.json.dumps(
                    {
                        'runId': run.run_id,
                        'repositoryName': external_pipeline.handle.repository_name,
                        'repositoryLocationName': external_pipeline.handle.location_name,
                    }
                ),
            ],
            job_name=job_name,
            pod_name=pod_name,
            component='runmaster',
        )

        job_namespace = exc_config.get('job_namespace')

        api = kubernetes.client.BatchV1Api()
        api.create_namespaced_job(body=job, namespace=job_namespace)

        instance.report_engine_event(
            'Kubernetes runmaster job launched',
            run,
            EngineEventData(
                [
                    EventMetadataEntry.text(job_name, 'Kubernetes Job name'),
                    EventMetadataEntry.text(pod_name, 'Kubernetes Pod name'),
                    EventMetadataEntry.text(job_namespace, 'Kubernetes Namespace'),
                    EventMetadataEntry.text(run.run_id, 'Run ID'),
                ]
            ),
            cls=CeleryK8sRunLauncher,
        )
        return run

    def can_terminate(self, run_id):
        check.str_param(run_id, 'run_id')
        return False

    def terminate(self, run_id):
        check.str_param(run_id, 'run_id')
        check.not_implemented('Termination not yet implemented')


def _get_validated_celery_k8s_executor_config(run_config):
    check.dict_param(run_config, 'run_config')

    try:
        from dagster_celery.executor_k8s import CELERY_K8S_CONFIG_KEY, celery_k8s_config
    except ImportError:
        raise DagsterK8sError(
            'To use the CeleryK8sRunLauncher, dagster_celery must be'
            ' installed in your Python environment.'
        )

    check.invariant(
        CELERY_K8S_CONFIG_KEY in run_config.get('execution', {}),
        '{} execution must be configured in pipeline execution config to launch runs with '
        'CeleryK8sRunLauncher'.format(CELERY_K8S_CONFIG_KEY),
    )

    execution_config_schema = resolve_to_config_type(celery_k8s_config())
    execution_run_config = run_config['execution'][CELERY_K8S_CONFIG_KEY].get('config', {})
    res = process_config(execution_config_schema, execution_run_config)

    check.invariant(
        res.success, 'Incorrect {} execution schema provided'.format(CELERY_K8S_CONFIG_KEY)
    )

    return res.value
