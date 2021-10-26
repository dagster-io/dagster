from dagster import op, Any, In, Nothing, OpDefinition, Out
import logging
import time
import os

from airflow.models import Connection
from airflow import settings
from airflow.utils.db import initdb


def create_conn(username, password, host=None):
    new_conn = Connection(conn_id=f'http_default', login=username, host=host if host else None)
    new_conn.set_password(password)

    session = settings.Session()
    session.add(new_conn)
    session.commit()


def operator_to_op(
    airflow_op,
    capture_python_logs=False,
    return_output=False,
    connections: Optional[List[Connection]] = None,
) -> OpDefinition:

    os.environ[
        "AIRFLOW_CONN_HTTP_DEFAULT"
    ] = 'http://username:password@mycoolwebsite.com/https?headers=header'

    @op(ins={"start_after": In(Nothing)}, out=Out(Any) if return_output else Out(Nothing))
    def converted_op(context):
        airflow_op._log = context.log
        if capture_python_logs:
            root_logger = logging.getLogger()
            root_logger.addHandler(context.log._dagster_handler)
            print("y" * 10)
            print(root_logger.handlers)

        start = time.time()
        # settings.SQL_ALCHEMY_CONN = "sqlite://"
        # settings.configure_orm()
        # initdb()
        end = time.time()
        print("time diff", end - start)
        # create_conn("foo", "bar", "https://myfakeurl.com")
        output = airflow_op.execute({})
        if capture_python_logs:
            root_logger.removeHandler(context.log._dagster_handler)
        if return_output:
            return output

    return converted_op
