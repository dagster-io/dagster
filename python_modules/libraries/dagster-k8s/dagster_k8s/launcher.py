from kubernetes import client, config

from dagster import Field
from dagster import __version__ as dagster_version
from dagster import check
from dagster.core.instance import DagsterInstance
from dagster.core.launcher import RunLauncher
from dagster.core.serdes import ConfigurableClass, ConfigurableClassData
from dagster.core.storage.pipeline_run import PipelineRun
from dagster.seven import json

BACKOFF_LIMIT = 4

TTL_SECONDS_AFTER_FINISHED = 100


class K8sRunLauncher(RunLauncher, ConfigurableClass):
    '''RunLauncher that starts a per-run Kubernetes Job.
    
    Args:
        service_account_name (str): The name of the Kubernetes service account under which to run
            the Job.
        job_image (str): The name of the image to run in the Job -- must respond to
            ``dagster-graphql -q`` invocations
        instance_config_map (str): The ``name`` of an existing Volume to mount into the pod in
            order to provide a ConfigMap for the Dagster instance.
        load_kubeconfig (Optional[bool]): If ``True``, will load k8s config from the file specified
            in ``kubeconfig_file`` (using ``kubernetes.config.load_kube_config``). Otherwise, we
            assume the launcher is running in-cluster and load config using
            ``kubernetes.config.load_incluster_config``. Default: ``False``.
        kubeconfig_file (Optional[str]): The kubeconfig file from which to load config. Required if
            ``load_kubeconfig`` is ``True``.
        image_pull_secrets (Optional[List[Dict[str, str]]]): Optionally, a list of dicts, each of
            which expresses a Kubernetes ``LocalObjectReference`` (e.g.,
            ``{'name': 'myRegistryName'}``). This allows you to specify the ```imagePullSecrets`` on
            a pod basis. Typically, these will be provided through the service account, when needed.
            See:
            https://kubernetes.io/docs/concepts/containers/images/#specifying-imagepullsecrets-on-a-pod
            and https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.17/#podspec-v1-core.
        image_pull_policy (Optional[str]): Allows the image pull policy to be overridden, e.g. to
            enable local testing with kind. Default: ``'Always'``.
    '''

    def __init__(
        self,
        service_account_name,
        job_image,
        instance_config_map,
        image_pull_policy='Always',
        image_pull_secrets=None,
        load_kubeconfig=False,
        kubeconfig_file=None,
        inst_data=None,
    ):
        self._inst_data = check.opt_inst_param(inst_data, 'inst_data', ConfigurableClassData)
        self.job_image = check.str_param(job_image, 'job_image')
        self.instance_config_map = check.str_param(instance_config_map, 'instance_config_map')
        self.image_pull_secrets = check.opt_list_param(image_pull_secrets, 'image_pull_secrets')
        self.image_pull_policy = check.str_param(image_pull_policy, 'image_pull_policy')
        self.service_account_name = check.str_param(service_account_name, 'service_account_name')
        check.bool_param(load_kubeconfig, 'load_kubeconfig')
        if load_kubeconfig:
            check.str_param(kubeconfig_file, 'kubeconfig_file')
        else:
            check.invariant(
                kubeconfig_file is None, '`kubeconfig_file` is set but `load_kubeconfig` is True.'
            )

        if load_kubeconfig:
            config.load_kube_config(kubeconfig_file)
        else:
            config.load_incluster_config()

        self._kube_api = client.BatchV1Api()

    @classmethod
    def config_type(cls):
        return {
            'service_account_name': str,
            'job_image': str,
            'instance_config_map': str,
            'image_pull_secrets': Field(list, is_optional=True),
            'image_pull_policy': Field(str, is_optional=True, default_value='Always'),
        }

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data, **config_value)

    @property
    def inst_data(self):
        return self._inst_data

    def construct_job(self, run):
        check.inst_param(run, 'run', PipelineRun)

        dagster_labels = {
            'app.kubernetes.io/name': 'dagster',
            'app.kubernetes.io/instance': 'dagster',
            'app.kubernetes.io/version': dagster_version,
        }

        execution_params = {
            'executionParams': {
                'selector': run.selector.to_graphql_input(),
                "environmentConfigData": run.environment_dict,
                'executionMetadata': {"runId": run.run_id},
                "mode": run.mode,
            },
        }

        job_container = client.V1Container(
            name='dagster-job-%s' % run.run_id,
            image=self.job_image,
            command=['dagster-graphql'],
            args=["-p", "executePlan", "-v", json.dumps(execution_params)],
            image_pull_policy=self.image_pull_policy,
            env=[client.V1EnvVar(name='DAGSTER_HOME', value='/opt/dagster/dagster_home')],
            volume_mounts=[
                client.V1VolumeMount(
                    name='dagster-instance',
                    mount_path='/opt/dagster/dagster_home/dagster.yaml',
                    sub_path='dagster.yaml',
                )
            ],
        )

        config_map_volume = client.V1Volume(
            name='dagster-instance',
            config_map=client.V1ConfigMapVolumeSource(name=self.instance_config_map),
        )

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                name='dagster-job-pod-%s' % run.run_id, labels=dagster_labels
            ),
            spec=client.V1PodSpec(
                image_pull_secrets=self.image_pull_secrets,
                service_account_name=self.service_account_name,
                restart_policy='Never',
                containers=[job_container],
                volumes=[config_map_volume],
            ),
        )

        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name='dagster-job-%s' % run.run_id, labels=dagster_labels),
            spec=client.V1JobSpec(
                template=template,
                backoff_limit=BACKOFF_LIMIT,
                ttl_seconds_after_finished=TTL_SECONDS_AFTER_FINISHED,
            ),
        )
        return job

    def launch_run(self, instance, run):
        check.inst_param(run, 'run', PipelineRun)
        check.inst_param(instance, 'instance', DagsterInstance)

        instance.create_run(run)
        job = self.construct_job(run)
        api_response = self._kube_api.create_namespaced_job(body=job, namespace="default")
        # FIXME add an event here
        print("Job created. status='%s'" % str(api_response.status))
        return run
