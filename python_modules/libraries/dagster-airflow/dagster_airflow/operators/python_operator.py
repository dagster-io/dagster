'''The dagster-airflow operators.'''
import logging

from airflow.exceptions import AirflowException
from dagster_airflow.vendor.python_operator import PythonOperator
from dagster_graphql.client.mutations import execute_execute_plan_mutation
from dagster_graphql.client.query import EXECUTE_PLAN_MUTATION

from dagster import check, seven
from dagster.core.definitions.pipeline import ExecutionSelector
from dagster.core.instance import DagsterInstance
from dagster.core.storage.pipeline_run import PipelineRun, PipelineRunStatus

from .util import check_events_for_failures, check_events_for_skips, construct_variables


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
        instance_ref,
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
                'Executing GraphQL query: {query}\n'.format(query=EXECUTE_PLAN_MUTATION)
                + 'with variables:\n'
                + seven.json.dumps(redacted, indent=2)
            )
            instance = DagsterInstance.from_ref(instance_ref) if instance_ref else None
            if instance:
                instance.get_or_create_run(
                    PipelineRun(
                        pipeline_name=pipeline_name,
                        run_id=run_id,
                        environment_dict=environment_dict,
                        mode=mode,
                        selector=ExecutionSelector(pipeline_name),
                        step_keys_to_execute=None,
                        tags=None,
                        status=PipelineRunStatus.MANAGED,
                    )
                )

            events = execute_execute_plan_mutation(
                handle,
                construct_variables(mode, environment_dict, pipeline_name, run_id, ts, step_keys),
                instance_ref=instance_ref,
            )
            check_events_for_failures(events)
            check_events_for_skips(events)
            return events

        super(DagsterPythonOperator, self).__init__(
            task_id=task_id,
            provide_context=True,
            python_callable=python_callable,
            dag=dag,
            *args,
            **kwargs
        )
