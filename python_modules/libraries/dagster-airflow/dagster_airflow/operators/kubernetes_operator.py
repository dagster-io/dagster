import sys
import time

from airflow.contrib.kubernetes import kube_client, pod_generator, pod_launcher
from airflow.exceptions import AirflowException
from airflow.utils.state import State
from dagster_airflow.vendor.kubernetes_pod_operator import KubernetesPodOperator
from dagster_graphql.client.query import RAW_EXECUTE_PLAN_MUTATION

from dagster import __version__ as dagster_version
from dagster import check, seven
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.events import EngineEventData
from dagster.core.instance import DagsterInstance, InstanceRef
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus
from dagster.utils.error import serializable_error_info_from_exc_info

from .util import (
    check_events_for_failures,
    check_events_for_skips,
    construct_variables,
    get_aws_environment,
    parse_raw_res,
)

# For retries on log retrieval
LOG_RETRIEVAL_MAX_ATTEMPTS = 5
LOG_RETRIEVAL_WAITS_BETWEEN_ATTEMPTS_SEC = 5


class DagsterKubernetesPodOperator(KubernetesPodOperator):
    '''Dagster operator for Apache Airflow.

    Wraps a modified KubernetesPodOperator.
    '''

    # py2 compat
    # pylint: disable=keyword-arg-before-vararg
    def __init__(
        self,
        task_id,
        environment_dict=None,
        pipeline_name=None,
        mode=None,
        step_keys=None,
        dag=None,
        instance_ref=None,
        *args,
        **kwargs
    ):
        check.str_param(pipeline_name, 'pipeline_name')
        step_keys = check.opt_list_param(step_keys, 'step_keys', of_type=str)
        environment_dict = check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)
        check.opt_inst_param(instance_ref, 'instance_ref', InstanceRef)

        kwargs['name'] = 'dagster.{pipeline_name}.{task_id}'.format(
            pipeline_name=pipeline_name, task_id=task_id
        ).replace(
            '_', '-'  # underscores are not permissible DNS names
        )

        if 'storage' not in environment_dict:
            raise AirflowException(
                'No storage config found -- must configure either filesystem or s3 storage for '
                'the DagsterKubernetesPodOperator. Ex.: \n'
                'storage:\n'
                '  filesystem:\n'
                '    base_dir: \'/some/shared/volume/mount/special_place\''
                '\n\n --or--\n\n'
                'storage:\n'
                '  s3:\n'
                '    s3_bucket: \'my-s3-bucket\'\n'
            )

        check.invariant(
            'in_memory' not in environment_dict.get('storage', {}),
            'Cannot use in-memory storage with Airflow, must use S3',
        )

        self.environment_dict = environment_dict
        self.pipeline_name = pipeline_name
        self.mode = mode
        self.step_keys = step_keys
        self._run_id = None
        # self.instance might be None in, for instance, a unit test setting where the operator
        # was being directly instantiated without passing through make_airflow_dag
        self.instance = DagsterInstance.from_ref(instance_ref) if instance_ref else None

        # Store Airflow DAG run timestamp so that we can pass along via execution metadata
        self.airflow_ts = kwargs.get('ts')

        # Add AWS creds
        self.env_vars = kwargs.get('env_vars', {})
        for k, v in get_aws_environment().items():
            self.env_vars.setdefault(k, v)

        kwargs.setdefault('labels', {})
        kwargs['labels'].setdefault('dagster_pipeline', self.pipeline_name)
        kwargs['labels'].setdefault('app.kubernetes.io/name', 'dagster')
        kwargs['labels'].setdefault('app.kubernetes.io/instance', self.pipeline_name)
        kwargs['labels'].setdefault('app.kubernetes.io/version', dagster_version)
        kwargs['labels'].setdefault('app.kubernetes.io/component', 'pipeline-execution')
        kwargs['labels'].setdefault('app.kubernetes.io/part-of', 'dagster-airflow')
        kwargs['labels'].setdefault('app.kubernetes.io/managed-by', 'dagster-airflow')

        # The xcom mechanism for the pod operator is very unlike that of the Docker operator, so
        # we disable it
        if 'xcom_push' in kwargs:
            self.log.warning(
                'xcom_push cannot be enabled with the DagsterKubernetesPodOperator, disabling'
            )
        kwargs['xcom_push'] = False

        super(DagsterKubernetesPodOperator, self).__init__(
            task_id=task_id, dag=dag, *args, **kwargs
        )

    @property
    def run_id(self):
        return getattr(self, '_run_id', '')

    @property
    def query(self):
        # TODO: https://github.com/dagster-io/dagster/issues/1342
        redacted = construct_variables(
            self.mode, 'REDACTED', self.pipeline_name, self.run_id, self.airflow_ts, self.step_keys
        )
        self.log.info(
            'Executing GraphQL query: {query}\n'.format(query=RAW_EXECUTE_PLAN_MUTATION)
            + 'with variables:\n'
            + seven.json.dumps(redacted, indent=2)
        )

        variables = construct_variables(
            self.mode,
            self.environment_dict,
            self.pipeline_name,
            self.run_id,
            self.airflow_ts,
            self.step_keys,
        )

        return [
            'dagster-graphql',
            '-v',
            '{}'.format(seven.json.dumps(variables)),
            '-t',
            '{}'.format(RAW_EXECUTE_PLAN_MUTATION),
        ]

    def execute(self, context):
        try:
            from dagster_graphql.client.mutations import (
                DagsterGraphQLClientError,
                handle_execution_errors,
                handle_execute_plan_result_raw,
            )

        except ImportError:
            raise AirflowException(
                'To use the DagsterKubernetesPodOperator, dagster and dagster_graphql must be'
                ' installed in your Airflow environment.'
            )

        if 'run_id' in self.params:
            self._run_id = self.params['run_id']
        elif 'dag_run' in context and context['dag_run'] is not None:
            self._run_id = context['dag_run'].run_id

        # return to original execute code:
        try:
            client = kube_client.get_kube_client(
                in_cluster=self.in_cluster,
                cluster_context=self.cluster_context,
                config_file=self.config_file,
            )
            gen = pod_generator.PodGenerator()

            for mount in self.volume_mounts:
                gen.add_mount(mount)
            for volume in self.volumes:
                gen.add_volume(volume)

            pod = gen.make_pod(
                namespace=self.namespace,
                image=self.image,
                pod_id=self.name,
                cmds=self.cmds,
                arguments=self.query,
                labels=self.labels,
            )

            pod.service_account_name = self.service_account_name
            pod.secrets = self.secrets
            pod.envs = self.env_vars
            pod.image_pull_policy = self.image_pull_policy
            pod.image_pull_secrets = self.image_pull_secrets
            pod.annotations = self.annotations
            pod.resources = self.resources
            pod.affinity = self.affinity
            pod.node_selectors = self.node_selectors
            pod.hostnetwork = self.hostnetwork
            pod.tolerations = self.tolerations
            pod.configmaps = self.configmaps
            pod.security_context = self.security_context

            launcher = pod_launcher.PodLauncher(kube_client=client, extract_xcom=self.xcom_push)
            pipeline_run = PipelineRun(
                pipeline_name=self.pipeline_name,
                run_id=self.run_id,
                environment_dict=self.environment_dict,
                mode=self.mode,
                selector=ExecutionSelector(self.pipeline_name),
                step_keys_to_execute=None,
                tags=None,
                status=PipelineRunStatus.MANAGED,
            )
            try:
                if self.instance:
                    self.instance.get_or_create_run(pipeline_run)

                # we won't use the "result", which is the pod's xcom json file
                (final_state, _) = launcher.run_pod(
                    pod, startup_timeout=self.startup_timeout_seconds, get_logs=self.get_logs
                )

                # fetch the last line independently of whether logs were read
                # unbelievably, if you set tail_lines=1, the returned json has its double quotes
                # turned into unparseable single quotes
                res = None
                num_attempts = 0
                while not res and num_attempts < LOG_RETRIEVAL_MAX_ATTEMPTS:
                    raw_res = client.read_namespaced_pod_log(
                        name=pod.name, namespace=pod.namespace, container='base'
                    )
                    res = parse_raw_res(raw_res.split('\n'))
                    time.sleep(LOG_RETRIEVAL_WAITS_BETWEEN_ATTEMPTS_SEC)
                    num_attempts += 1
                    self.log.debug('k8s pod raw response: ' + str(raw_res))
                    self.log.debug('parsed response: ' + str(res))

                try:
                    handle_execution_errors(res, 'executePlan')
                except DagsterGraphQLClientError as err:
                    self.instance.report_engine_event(
                        self.__class__,
                        str(err),
                        pipeline_run,
                        EngineEventData.engine_error(
                            serializable_error_info_from_exc_info(sys.exc_info())
                        ),
                    )
                    raise

                events = handle_execute_plan_result_raw(res)

                if self.instance:
                    for event in events:
                        self.instance.handle_new_event(event)

                events = [e.dagster_event for e in events]
                check_events_for_failures(events)
                check_events_for_skips(events)
                return events

            finally:
                self._run_id = None

                if self.is_delete_operator_pod:
                    launcher.delete_pod(pod)

            if final_state != State.SUCCESS:
                raise AirflowException('Pod returned a failure: {state}'.format(state=final_state))
            # note the lack of returning the default xcom
        except AirflowException as ex:
            raise AirflowException('Pod Launching failed: {error}'.format(error=ex))
