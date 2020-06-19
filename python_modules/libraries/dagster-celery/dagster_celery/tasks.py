import hashlib

import six
from celery import Celery
from celery.utils.collections import force_mapping
from dagster_graphql.client.mutations import handle_execute_plan_result, handle_execution_errors
from dagster_graphql.client.util import parse_raw_log_lines
from kombu import Queue

from dagster import DagsterInstance, EventMetadataEntry, check, seven
from dagster.core.definitions.reconstructable import ReconstructablePipeline
from dagster.core.events import EngineEventData
from dagster.core.execution.api import create_execution_plan, execute_plan_iterator
from dagster.core.execution.retries import Retries
from dagster.core.instance import InstanceRef
from dagster.serdes import serialize_dagster_namedtuple
from dagster.seven import is_module_available

from .core_execution_loop import DELEGATE_MARKER
from .executor import CeleryExecutor


def create_task(celery_app, **task_kwargs):
    @celery_app.task(bind=True, name='execute_plan', **task_kwargs)
    def _execute_plan(_self, instance_ref_dict, executable_dict, run_id, step_keys, retries_dict):
        check.dict_param(instance_ref_dict, 'instance_ref_dict')
        check.dict_param(executable_dict, 'executable_dict')
        check.str_param(run_id, 'run_id')
        check.list_param(step_keys, 'step_keys', of_type=str)
        check.dict_param(retries_dict, 'retries_dict')

        instance_ref = InstanceRef.from_dict(instance_ref_dict)
        instance = DagsterInstance.from_ref(instance_ref)
        pipeline = ReconstructablePipeline.from_dict(executable_dict)
        retries = Retries.from_config(retries_dict)

        pipeline_run = instance.get_run_by_id(run_id)
        check.invariant(pipeline_run, 'Could not load run {}'.format(run_id))

        step_keys_str = ", ".join(step_keys)

        execution_plan = create_execution_plan(
            pipeline,
            pipeline_run.run_config,
            mode=pipeline_run.mode,
            step_keys_to_execute=pipeline_run.step_keys_to_execute,
        ).build_subset_plan(step_keys)

        engine_event = instance.report_engine_event(
            'Executing steps {} in celery worker'.format(step_keys_str),
            pipeline_run,
            EngineEventData(
                [EventMetadataEntry.text(step_keys_str, 'step_keys'),], marker_end=DELEGATE_MARKER,
            ),
            CeleryExecutor,
            step_key=execution_plan.step_key_for_single_step_plans(),
        )

        events = [engine_event]
        for step_event in execute_plan_iterator(
            execution_plan,
            pipeline_run=pipeline_run,
            run_config=pipeline_run.run_config,
            instance=instance,
            retries=retries,
        ):
            events.append(step_event)

        serialized_events = [serialize_dagster_namedtuple(event) for event in events]
        return serialized_events

    return _execute_plan


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
        from dagster_k8s import DagsterK8sJobConfig, construct_dagster_graphql_k8s_job
        from dagster_k8s.utils import get_pod_names_in_job, retrieve_pod_logs, wait_for_job_success
        from .executor_k8s import CeleryK8sJobExecutor

        import kubernetes

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


def make_app(app_args=None):
    app_ = Celery('dagster', **(app_args if app_args else {}))

    if app_args is None:
        app_.config_from_object('dagster_celery.defaults', force=True)

        if is_module_available('dagster_celery_config'):
            # pylint: disable=protected-access
            obj = force_mapping(app_.loader._smart_import('dagster_celery_config'))
            app_.conf.update(obj)

    app_.loader.import_module('celery.contrib.testing.tasks')

    app_.conf.task_queues = [
        Queue('dagster', routing_key='dagster.#', queue_arguments={'x-max-priority': 10})
    ]
    app_.conf.task_routes = {
        'execute_plan': {'queue': 'dagster', 'routing_key': 'dagster.execute_plan'},
        'execute_step_k8s_job': {'queue': 'dagster', 'routing_key': 'dagster.execute_step_k8s_job'},
    }
    app_.conf.task_queue_max_priority = 10
    app_.conf.task_default_priority = 5
    return app_


app = make_app()

execute_plan = create_task(app)
execute_step_k8s_job = create_k8s_job_task(app)


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
