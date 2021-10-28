from typing import List, Optional
from dagster import check, op, Any, In, Nothing, OpDefinition, Out
import logging
import os

from airflow.models import Connection
from airflow import settings
from airflow.utils.db import initdb


def operator_to_op(
    airflow_op,
    capture_python_logs=False,
    return_output=False,
    connections: Optional[List[Connection]] = None,
) -> OpDefinition:
    connections = check.opt_list_param(connections, "connections", Connection)

    for connection in connections:
        os.environ[f'AIRFLOW_CONN_{connection.conn_id}'.upper()] = connection.get_uri()

    @op(ins={"start_after": In(Nothing)}, out=Out(Any) if return_output else Out(Nothing))
    def converted_op(context):
        airflow_op._log = context.log
        if capture_python_logs:
            root_logger = logging.getLogger()
            root_logger.addHandler(context.log._dagster_handler)

        # settings.SQL_ALCHEMY_CONN = "sqlite://"
        # settings.configure_orm()
        # initdb()

        output = airflow_op.execute({})
        if capture_python_logs:
            root_logger.removeHandler(context.log._dagster_handler)
        if return_output:
            return output

    return converted_op
