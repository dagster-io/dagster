import logging
import os
from contextlib import contextmanager
from typing import List, Optional

from airflow.models import Connection
from airflow.models.baseoperator import BaseOperator

from dagster import Any, In, Nothing, OpDefinition, Out
from dagster import _check as check
from dagster import op


@contextmanager
def replace_airflow_logger_handlers(handler):
    try:
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        yield
    finally:
        root_logger.removeHandler(handler)


def airflow_operator_to_op(
    airflow_op: BaseOperator,
    connections: Optional[List[Connection]] = None,
    capture_python_logs=True,
    return_output=False,
) -> OpDefinition:
    """Construct a Dagster op corresponding to a given Airflow operator.

    The resulting op will execute the ``execute()`` method on the Airflow operator. Dagster and
    any dependencies required by the Airflow Operator must be available in the Python environment
    within which your Dagster ops execute.

    To specify Airflow connections utilized by the operator, instantiate and pass Airflow connection
    objects in a list to the ``connections`` parameter of this function.

    .. code-block:: python

        http_task = SimpleHttpOperator(task_id="my_http_task", endpoint="foo")
        connections = [Connection(conn_id="http_default", host="https://mycoolwebsite.com")]
        dagster_op = airflow_operator_to_op(http_task, connections=connections)

    In order to specify extra parameters to the connection, call the ``set_extra()`` method
    on the instantiated Airflow connection:

    .. code-block:: python

        s3_conn = Connection(conn_id=f's3_conn', conn_type="s3")
        s3_conn_extra = {
            "aws_access_key_id": "my_access_key",
            "aws_secret_access_key": "my_secret_access_key",
        }
        s3_conn.set_extra(json.dumps(s3_conn_extra))

    Args:
        airflow_op (BaseOperator): The Airflow operator to convert into a Dagster op
        connections (Optional[List[Connection]]): Airflow connections utilized by the operator.
        capture_python_logs (bool): If False, will not redirect Airflow logs to compute logs.
            (default: True)
        return_output (bool): If True, will return any output from the Airflow operator.
            (default: False)

    Returns:
        converted_op (OpDefinition): The generated Dagster op

    """
    airflow_op = check.inst_param(airflow_op, "airflow_op", BaseOperator)
    connections = check.opt_list_param(connections, "connections", Connection)

    @op(
        name=airflow_op.task_id,
        ins={"start_after": In(Nothing)},
        out=Out(Any) if return_output else Out(Nothing),
    )
    def converted_op(context):
        conn_names = []
        for connection in connections:
            conn_name = f"AIRFLOW_CONN_{connection.conn_id}".upper()
            os.environ[conn_name] = connection.get_uri()
            conn_names.append(conn_name)

        if capture_python_logs:
            # Airflow has local logging configuration that may set logging.Logger.propagate
            # to be false. We override the logger object and replace it with DagsterLogManager.
            airflow_op._log = context.log  # pylint: disable=protected-access
            # Airflow operators and hooks use separate logger objects. We add a handler to
            # receive logs from hooks.
            with replace_airflow_logger_handlers(
                context.log._dagster_handler  # pylint: disable=protected-access
            ):
                output = airflow_op.execute({})
        else:
            output = airflow_op.execute({})

        for conn_name in conn_names:
            os.environ.pop(conn_name)

        if return_output:
            return output

    return converted_op
