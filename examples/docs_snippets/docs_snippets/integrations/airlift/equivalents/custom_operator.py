# start_custom_op
from pathlib import Path

import boto3
from airflow.operators.python import PythonOperator


class UploadToS3Operator(PythonOperator):
    def __init__(self, path: str, *args, **kwargs) -> None:
        super().__init__(
            python_callable=self.upload_to_s3, op_args=[path], *args, **kwargs
        )

    def upload_to_s3(self, path: str) -> None:
        boto3.client("s3").upload_file(
            Filepath=path, Bucket="my_bucket", Key=Path(path).name
        )


# end_custom_op

# start_task
task = UploadToS3Operator(task_id="write_customers_data", path="path/to/customers.csv")
# end_task
