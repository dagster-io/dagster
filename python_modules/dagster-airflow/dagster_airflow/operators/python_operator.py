'''The dagster-airflow operators.'''
import logging

from airflow.exceptions import AirflowException

from dagster import check, seven
from dagster_airflow.vendor.python_operator import PythonOperator
from dagster_graphql.client.mutations import execute_start_pipeline_execution_query
from dagster_graphql.client.query import START_PIPELINE_EXECUTION_QUERY

from .util import construct_variables, skip_self_if_necessary


class DagsterPythonOperator(PythonOperator):
    def __init__(
        self,
        task_id,
        handle,
        pipeline_name,
        environment_dict,
        mode,
        step_keys,
        dag,
        *args,
        **kwargs
    ):
        if 'storage' not in environment_dict:
            raise AirflowException(
                'No storage config found -- must configure either filesystem or s3 storage for '
                'the DagsterPythonOperator. Ex.: \n'
                'storage:\n'
                '  filesystem:\n'
                '    base_dir: \'/tmp/special_place\''
                '\n\n --or--\n\n'
                'storage:\n'
                '  s3:\n'
                '    s3_bucket: \'my-s3-bucket\'\n'
            )

        check.invariant(
            'in_memory' not in environment_dict.get('storage', {}),
            'Cannot use in-memory storage with Airflow, must use filesystem or S3',
        )

        def python_callable(ts, dag_run, **kwargs):  # pylint: disable=unused-argument
            run_id = dag_run.run_id

            # TODO: https://github.com/dagster-io/dagster/issues/1342
            redacted = construct_variables(mode, 'REDACTED', pipeline_name, run_id, ts, step_keys)
            logging.info(
                'Executing GraphQL query: {query}\n'.format(query=START_PIPELINE_EXECUTION_QUERY)
                + 'with variables:\n'
                + seven.json.dumps(redacted, indent=2)
            )
            events = execute_start_pipeline_execution_query(
                handle,
                construct_variables(mode, environment_dict, pipeline_name, run_id, ts, step_keys),
            )

            skip_self_if_necessary(events)

            return events

        super(DagsterPythonOperator, self).__init__(
            task_id=task_id,
            provide_context=True,
            python_callable=python_callable,
            dag=dag,
            *args,
            **kwargs
        )
