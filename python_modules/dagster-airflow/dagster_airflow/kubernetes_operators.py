import json

from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
from airflow.contrib.kubernetes import kube_client, pod_generator, pod_launcher
from airflow.exceptions import AirflowException
from airflow.utils.state import State
from dagster import check
from .operators import DagsterSkipMixin, GenericExecMixin
from .util import airflow_storage_exception


class DagsterKubernetesPodOperator(GenericExecMixin, KubernetesPodOperator, DagsterSkipMixin):
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
        *args,
        **kwargs
    ):

        # TODO: reduce boilerplate
        check.str_param(pipeline_name, 'pipeline_name')
        step_keys = check.opt_list_param(step_keys, 'step_keys', of_type=str)
        environment_dict = check.opt_dict_param(environment_dict, 'environment_dict', key_type=str)

        if 'storage' not in environment_dict:
            # TODO: there's no meaningful /tmp dir, but also, shared k8s vols don't exist
            # without a significant amount of extra work
            raise airflow_storage_exception("/path-to-your-shared-kubernetes-volume")

        check.invariant(
            'in_memory' not in environment_dict.get('storage', {}),
            'Cannot use in-memory storage with Airflow, must use S3',
        )

        # TODO: decide whether any of this CRUD can go into a base class too
        self.environment_dict = environment_dict
        self.pipeline_name = pipeline_name
        self.mode = mode
        self.step_keys = step_keys
        self._run_id = None

        # Store Airflow DAG run timestamp so that we can pass along via execution metadata
        self.airflow_ts = kwargs.get('ts')

        # TODO: don't blow away S3 creds on providing an env
        if 'env_vars' not in kwargs:
            kwargs['env_vars'] = self.default_environment

        super(DagsterKubernetesPodOperator, self).__init__(
            task_id=task_id, dag=dag, *args, **kwargs
        )

    def execute(self, context):
        try:
            from dagster_graphql.client.mutations import (
                handle_start_pipeline_execution_errors,
                handle_start_pipeline_execution_result,
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
                arguments=self.arguments,
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
            try:
                # we won't use the "result", which is the returned pod object
                (final_state, _) = launcher.run_pod(
                    pod, startup_timeout=self.startup_timeout_seconds, get_logs=self.get_logs
                )

                # fetch the last line independently of whether logs were read
                dagster_json_line = client.read_namespaced_pod_log(
                    name=pod.name, namespace=pod.namespace, container='base', tail_lines=1
                )

                # read the last line directly as json
                # TODO: handle bytes type?
                # TODO: handle garbage API string responses
                res = json.loads(dagster_json_line)
                handle_start_pipeline_execution_errors(res)
                events = handle_start_pipeline_execution_result(res)

                self.skip_self_if_necessary(events, context['execution_date'], context['task'])

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
