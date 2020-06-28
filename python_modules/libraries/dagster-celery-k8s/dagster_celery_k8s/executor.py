import hashlib

import kubernetes
import six
from dagster_celery.config import DEFAULT_CONFIG, dict_wrapper
from dagster_celery.core_execution_loop import DELEGATE_MARKER
from dagster_celery.defaults import broker_url, result_backend
from dagster_graphql.client.mutations import handle_execute_plan_result, handle_execution_errors
from dagster_graphql.client.util import parse_raw_log_lines
from dagster_k8s import DagsterK8sJobConfig, construct_dagster_graphql_k8s_job
from dagster_k8s.job import get_k8s_resource_requirements
from dagster_k8s.utils import get_pod_names_in_job, retrieve_pod_logs, wait_for_job_success

from dagster import DagsterInstance, EventMetadataEntry, Executor, check, executor, seven
from dagster.core.definitions.executor import check_cross_process_constraints
from dagster.core.events import EngineEventData
from dagster.core.execution.retries import Retries
from dagster.core.instance import InstanceRef
from dagster.serdes import serialize_dagster_namedtuple

from .config import CELERY_K8S_CONFIG_KEY, celery_k8s_config
from .launcher import CeleryK8sRunLauncher


@executor(name=CELERY_K8S_CONFIG_KEY, config_schema=celery_k8s_config())
def celery_k8s_job_executor(init_context):
    '''Celery-based executor which launches tasks as Kubernetes Jobs.

    The Celery executor exposes config settings for the underlying Celery app under
    the ``config_source`` key. This config corresponds to the "new lowercase settings" introduced
    in Celery version 4.0 and the object constructed from config will be passed to the
    :py:class:`celery.Celery` constructor as its ``config_source`` argument.
    (See https://docs.celeryproject.org/en/latest/userguide/configuration.html for details.)

    The executor also exposes the ``broker``, `backend`, and ``include`` arguments to the
    :py:class:`celery.Celery` constructor.

    In the most common case, you may want to modify the ``broker`` and ``backend`` (e.g., to use
    Redis instead of RabbitMQ). We expect that ``config_source`` will be less frequently
    modified, but that when solid executions are especially fast or slow, or when there are
    different requirements around idempotence or retry, it may make sense to execute pipelines
    with variations on these settings.

    If you'd like to configure a Celery Kubernetes Job executor in addition to the
    :py:class:`~dagster.default_executors`, you should add it to the ``executor_defs`` defined on a
    :py:class:`~dagster.ModeDefinition` as follows:

    .. code-block:: python

        from dagster import ModeDefinition, default_executors, pipeline
        from dagster_celery.executor_k8s import celery_k8s_job_executor

        @pipeline(mode_defs=[
            ModeDefinition(executor_defs=default_executors + [celery_k8s_job_executor])
        ])
        def celery_enabled_pipeline():
            pass

    Then you can configure the executor as follows:

    .. code-block:: YAML

        execution:
          celery-k8s:
            config:
              job_image: 'my_repo.com/image_name:latest'
              job_namespace: 'some-namespace'
              broker: 'pyamqp://guest@localhost//'  # Optional[str]: The URL of the Celery broker
              backend: 'rpc://' # Optional[str]: The URL of the Celery results backend
              include: ['my_module'] # Optional[List[str]]: Modules every worker should import
              config_source: # Dict[str, Any]: Any additional parameters to pass to the
                  #...       # Celery workers. This dict will be passed as the `config_source`
                  #...       # argument of celery.Celery().

    Note that the YAML you provide here must align with the configuration with which the Celery
    workers on which you hope to run were started. If, for example, you point the executor at a
    different broker than the one your workers are listening to, the workers will never be able to
    pick up tasks for execution.

    In deployments where the celery_k8s_job_executor is used all appropriate celery and dagster_celery
    commands must be invoked with the `-A dagster_celery_k8s.app` argument.
    '''

    check_cross_process_constraints(init_context)

    run_launcher = init_context.instance.run_launcher
    exc_cfg = init_context.executor_config

    check.inst(
        run_launcher,
        CeleryK8sRunLauncher,
        'This engine is only compatible with a CeleryK8sRunLauncher; configure the '
        'CeleryK8sRunLauncher on your instance to use it.',
    )

    job_config = DagsterK8sJobConfig(
        dagster_home=run_launcher.dagster_home,
        instance_config_map=run_launcher.instance_config_map,
        postgres_password_secret=run_launcher.postgres_password_secret,
        job_image=exc_cfg.get('job_image'),
        image_pull_policy=exc_cfg.get('image_pull_policy'),
        image_pull_secrets=exc_cfg.get('image_pull_secrets'),
        service_account_name=exc_cfg.get('service_account_name'),
        env_config_maps=exc_cfg.get('env_config_maps'),
        env_secrets=exc_cfg.get('env_secrets'),
    )

    # Set on the instance but overrideable here
    broker = run_launcher.broker or exc_cfg.get('broker')
    backend = run_launcher.backend or exc_cfg.get('backend')
    config_source = run_launcher.config_source or exc_cfg.get('config_source')
    include = run_launcher.include or exc_cfg.get('include')
    retries = run_launcher.retries or Retries.from_config(exc_cfg.get('retries'))

    return CeleryK8sJobExecutor(
        broker=broker,
        backend=backend,
        config_source=config_source,
        include=include,
        retries=retries,
        job_config=job_config,
        job_namespace=exc_cfg.get('job_namespace'),
        load_incluster_config=exc_cfg.get('load_incluster_config'),
        kubeconfig_file=exc_cfg.get('kubeconfig_file'),
        repo_location_name=exc_cfg.get('repo_location_name'),
    )


class CeleryK8sJobExecutor(Executor):
    def __init__(
        self,
        retries,
        broker=None,
        backend=None,
        include=None,
        config_source=None,
        job_config=None,
        job_namespace=None,
        load_incluster_config=False,
        kubeconfig_file=None,
        repo_location_name=None,
    ):

        if load_incluster_config:
            check.invariant(
                kubeconfig_file is None,
                '`kubeconfig_file` is set but `load_incluster_config` is True.',
            )
        else:
            check.opt_str_param(kubeconfig_file, 'kubeconfig_file')

        self.retries = check.inst_param(retries, 'retries', Retries)
        self.broker = check.opt_str_param(broker, 'broker', default=broker_url)
        self.backend = check.opt_str_param(backend, 'backend', default=result_backend)
        self.include = check.opt_list_param(include, 'include', of_type=str)
        self.config_source = dict_wrapper(
            dict(DEFAULT_CONFIG, **check.opt_dict_param(config_source, 'config_source'))
        )
        self.job_config = check.inst_param(job_config, 'job_config', DagsterK8sJobConfig)
        self.job_namespace = check.opt_str_param(job_namespace, 'job_namespace', default='default')

        self.load_incluster_config = check.bool_param(
            load_incluster_config, 'load_incluster_config'
        )

        self.kubeconfig_file = check.opt_str_param(kubeconfig_file, 'kubeconfig_file')
        self.repo_location_name = check.str_param(repo_location_name, 'repo_location_name')

    def execute(self, pipeline_context, execution_plan):
        from dagster_celery.core_execution_loop import core_celery_execution_loop

        return core_celery_execution_loop(
            pipeline_context, execution_plan, step_execution_fn=_submit_task_k8s_job
        )

    def app_args(self):
        return {
            'broker': self.broker,
            'backend': self.backend,
            'include': self.include,
            'config_source': self.config_source,
            'retries': self.retries,
        }


def _submit_task_k8s_job(app, pipeline_context, step, queue, priority):
    resources = get_k8s_resource_requirements(step.tags)
    task = create_k8s_job_task(app)

    recon_repo = pipeline_context.pipeline.get_reconstructable_repository()

    task_signature = task.si(
        instance_ref_dict=pipeline_context.instance.get_ref().to_dict(),
        step_keys=[step.key],
        run_config=pipeline_context.pipeline_run.run_config,
        mode=pipeline_context.pipeline_run.mode,
        repo_name=recon_repo.get_definition().name,
        repo_location_name=pipeline_context.executor.repo_location_name,
        run_id=pipeline_context.pipeline_run.run_id,
        job_config_dict=pipeline_context.executor.job_config.to_dict(),
        job_namespace=pipeline_context.executor.job_namespace,
        resources=resources,
        retries_dict=pipeline_context.executor.retries.for_inner_plan().to_config(),
        load_incluster_config=pipeline_context.executor.load_incluster_config,
        kubeconfig_file=pipeline_context.executor.kubeconfig_file,
    )

    return task_signature.apply_async(
        priority=priority,
        queue=queue,
        routing_key='{queue}.execute_step_k8s_job'.format(queue=queue),
    )


def create_k8s_job_task(celery_app, **task_kwargs):
    @celery_app.task(bind=True, name='execute_step_k8s_job', **task_kwargs)
    def _execute_step_k8s_job(
        _self,
        instance_ref_dict,
        step_keys,
        run_config,
        mode,
        repo_name,
        repo_location_name,
        run_id,
        job_config_dict,
        job_namespace,
        load_incluster_config,
        retries_dict,
        resources=None,
        kubeconfig_file=None,
    ):
        '''Run step execution in a K8s job pod.
        '''

        check.dict_param(instance_ref_dict, 'instance_ref_dict')
        check.list_param(step_keys, 'step_keys', of_type=str)
        check.invariant(
            len(step_keys) == 1, 'Celery K8s task executor can only execute 1 step at a time'
        )
        check.dict_param(run_config, 'run_config')
        check.str_param(mode, 'mode')
        check.str_param(repo_name, 'repo_name')
        check.str_param(repo_location_name, 'repo_location_name')
        check.str_param(run_id, 'run_id')

        # Celery will serialize this as a list
        job_config = DagsterK8sJobConfig.from_dict(job_config_dict)
        check.inst_param(job_config, 'job_config', DagsterK8sJobConfig)
        check.str_param(job_namespace, 'job_namespace')
        check.bool_param(load_incluster_config, 'load_incluster_config')
        check.dict_param(retries_dict, 'retries_dict')

        check.opt_dict_param(resources, 'resources', key_type=str, value_type=dict)
        check.opt_str_param(kubeconfig_file, 'kubeconfig_file')

        # For when launched via DinD or running the cluster
        if load_incluster_config:
            kubernetes.config.load_incluster_config()
        else:
            kubernetes.config.load_kube_config(kubeconfig_file)

        instance_ref = InstanceRef.from_dict(instance_ref_dict)
        instance = DagsterInstance.from_ref(instance_ref)
        pipeline_run = instance.get_run_by_id(run_id)
        check.invariant(pipeline_run, 'Could not load run {}'.format(run_id))

        step_keys_str = ", ".join(step_keys)

        # Ensure we stay below k8s name length limits
        k8s_name_key = _get_k8s_name_key(run_id, step_keys)

        retries = Retries.from_config(retries_dict)

        if retries.get_attempt_count(step_keys[0]):
            attempt_number = retries.get_attempt_count(step_keys[0])
            job_name = 'dagster-job-%s-%d' % (k8s_name_key, attempt_number)
            pod_name = 'dagster-job-%s-%d' % (k8s_name_key, attempt_number)
        else:
            job_name = 'dagster-job-%s' % (k8s_name_key)
            pod_name = 'dagster-job-%s' % (k8s_name_key)

        variables = {
            'executionParams': {
                'runConfigData': run_config,
                'mode': mode,
                'selector': {
                    'repositoryLocationName': repo_location_name,
                    'repositoryName': repo_name,
                    'pipelineName': pipeline_run.pipeline_name,
                },
                'executionMetadata': {'runId': run_id},
                'stepKeys': step_keys,
            },
            'retries': retries.to_graphql_input(),
        }
        args = ['-p', 'executePlan', '-v', seven.json.dumps(variables)]

        job = construct_dagster_graphql_k8s_job(job_config, args, job_name, resources, pod_name)

        # Running list of events generated from this task execution
        events = []

        # Post event for starting execution
        engine_event = instance.report_engine_event(
            'Executing steps {} in Kubernetes job {}'.format(step_keys_str, job.metadata.name),
            pipeline_run,
            EngineEventData(
                [
                    EventMetadataEntry.text(step_keys_str, 'Step keys'),
                    EventMetadataEntry.text(job.metadata.name, 'Kubernetes Job name'),
                    EventMetadataEntry.text(pod_name, 'Kubernetes Pod name'),
                    EventMetadataEntry.text(job_config.job_image, 'Job image'),
                    EventMetadataEntry.text(job_config.image_pull_policy, 'Image pull policy'),
                    EventMetadataEntry.text(
                        str(job_config.image_pull_secrets), 'Image pull secrets'
                    ),
                    EventMetadataEntry.text(
                        str(job_config.service_account_name), 'Service account name'
                    ),
                ],
                marker_end=DELEGATE_MARKER,
            ),
            CeleryK8sJobExecutor,
            # validated above that step_keys is length 1, and it is not possible to use ETH or
            # execution plan in this function (Celery K8s workers should not access to user code)
            step_key=step_keys[0],
        )
        events.append(engine_event)

        kubernetes.client.BatchV1Api().create_namespaced_job(body=job, namespace=job_namespace)

        wait_for_job_success(job.metadata.name, namespace=job_namespace)
        pod_names = get_pod_names_in_job(job.metadata.name, namespace=job_namespace)

        # Post engine event for log retrieval
        engine_event = instance.report_engine_event(
            'Retrieving logs from Kubernetes Job pods',
            pipeline_run,
            EngineEventData([EventMetadataEntry.text('\n'.join(pod_names), 'Pod names')]),
            CeleryK8sJobExecutor,
            step_key=step_keys[0],
        )
        events.append(engine_event)

        logs = []
        for pod_name in pod_names:
            raw_logs = retrieve_pod_logs(pod_name, namespace=job_namespace)
            logs += raw_logs.split('\n')

        res = parse_raw_log_lines(logs)
        handle_execution_errors(res, 'executePlan')
        step_events = handle_execute_plan_result(res)

        events += step_events

        serialized_events = [serialize_dagster_namedtuple(event) for event in events]
        return serialized_events

    return _execute_step_k8s_job


def _get_k8s_name_key(run_id, step_keys):
    '''Creates a unique (short!) identifier to name k8s objects based on run ID and step key(s).

    K8s Job names are limited to 63 characters, because they are used as labels. For more info, see:

    https://kubernetes.io/docs/concepts/overview/working-with-objects/names/
    '''
    check.str_param(run_id, 'run_id')
    check.list_param(step_keys, 'step_keys', of_type=str)

    # Creates 32-bit signed int, so could be negative
    name_hash = hashlib.md5(six.ensure_binary(run_id + '-'.join(step_keys)))

    return name_hash.hexdigest()
