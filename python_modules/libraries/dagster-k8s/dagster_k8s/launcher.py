import kubernetes

from dagster import EventMetadataEntry, Field, Noneable, StringSource, check, seven
from dagster.core.events import EngineEventData
from dagster.core.host_representation import ExternalPipeline
from dagster.core.instance import DagsterInstance
from dagster.core.launcher import RunLauncher
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.serdes import ConfigurableClass, ConfigurableClassData
from dagster.utils import frozentags, merge_dicts

from .job import (
    DagsterK8sJobConfig,
    construct_dagster_graphql_k8s_job,
    get_k8s_resource_requirements,
)


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

        resources = get_k8s_resource_requirements(frozentags(external_pipeline.tags))

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
            resources=resources,
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
