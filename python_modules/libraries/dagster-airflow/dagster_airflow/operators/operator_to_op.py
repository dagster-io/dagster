from typing import List, Optional
from dagster import check, op, Any, In, Nothing, OpDefinition, Out
import logging
import os
from contextlib import contextmanager

from airflow.models import Connection
from airflow import settings
from airflow.utils.db import initdb


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
    accept_input=False,
    return_output=False,
) -> OpDefinition:
    connections = check.opt_list_param(connections, "connections", Connection)

    for connection in connections:
        os.environ[f'AIRFLOW_CONN_{connection.conn_id}'.upper()] = connection.get_uri()

    @op(
        name=airflow_op.task_id,
        ins={"start_after": In(Nothing)},
        out=Out(Any) if return_output else Out(Nothing),
    )
    def converted_op(context):
        if capture_python_logs:
            airflow_op._log = context.log
            with replace_airflow_logger_handlers(context.log._dagster_handler):
                output = airflow_op.execute({})
        else:
            output = airflow_op.execute({})

        if return_output:
            return output

    return converted_op
