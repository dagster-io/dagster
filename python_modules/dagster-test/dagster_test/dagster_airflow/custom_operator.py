import logging

from dagster_airflow.operators.util import invoke_steps_within_python_operator
from dagster_airflow.vendor.python_operator import PythonOperator

# Template for creating a custom dagster operator that wraps Airflow PythonOperator.
# To use, copy this file and stub out lines 14 - 17 with custom logic


class CustomOperator(PythonOperator):
    def __init__(self, dagster_operator_parameters, *args, **kwargs):
        def python_callable(ts, dag_run, **kwargs):  # pylint: disable=unused-argument

            # Add custom logic here
            logger = logging.getLogger("CustomOperatorLogger")
            logger.setLevel(logging.INFO)
            logger.info("CustomOperator is called")

            return invoke_steps_within_python_operator(
                dagster_operator_parameters.invocation_args, ts, dag_run, **kwargs
            )

        super(CustomOperator, self).__init__(
            task_id=dagster_operator_parameters.task_id,
            provide_context=True,
            python_callable=python_callable,
            dag=dagster_operator_parameters.dag,
            *args,
            **kwargs
        )
