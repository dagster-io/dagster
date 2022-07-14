import json

from airflow.models import Connection
from airflow.operators.http_operator import SimpleHttpOperator
from dagster import job
from dagster_airflow import airflow_operator_to_op

# start_operator_to_op_1
http_task = SimpleHttpOperator(task_id="http_task", method="GET", endpoint="images")
connections = [Connection(conn_id="http_default", host="https://google.com")]
dagster_op = airflow_operator_to_op(http_task, connections=connections)


@job
def my_http_job():
    dagster_op()


# end_operator_to_op_1

# start_operator_to_op_2
s3_conn = Connection(conn_id=f"s3_conn", conn_type="s3")
s3_conn.set_extra(
    json.dumps(
        {
            "aws_access_key_id": "my_access_key",
            "aws_secret_access_key": "my_secret_key",
        }
    )
)
# end_operator_to_op_2
