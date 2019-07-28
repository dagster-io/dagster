from airflow.contrib.operators.kubernetes_pod_operator import KubernetesPodOperator
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
