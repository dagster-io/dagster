import logging
import os
from contextlib import contextmanager
from typing import List, Optional

from airflow.models import Connection
from dagster import check, op, Any, In, Nothing, OpDefinition, Out


@contextmanager
def replace_airflow_logger_handlers(handler):
    try:
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        yield
    finally:
        root_logger.removeHandler(handler)


def operator_to_op(
    airflow_op,
    connections: Optional[List[Connection]] = None,
    capture_python_logs=True,
    return_output=False,
) -> OpDefinition:
    connections = check.opt_list_param(connections, "connections", Connection)

    for connection in connections:
        os.environ[f"AIRFLOW_CONN_{connection.conn_id}".upper()] = connection.get_uri()

    @op(
        name=airflow_op.task_id,
        ins={"start_after": In(Nothing)},
        out=Out(Any) if return_output else Out(Nothing),
    )
    def converted_op(context):
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

        if return_output:
            return output

    return converted_op
