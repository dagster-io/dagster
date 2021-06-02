import moto
from dagster import execute_pipeline
from docs_snippets.guides.file_io_manager import file_pipeline, s3_client


def test_file_pipeline_dev():
    execute_pipeline(file_pipeline, mode="dev")


def test_file_pipeline_prod():
    with moto.mock_s3():
        s3_client().create_bucket(Bucket="my_bucket")
        execute_pipeline(file_pipeline, mode="prod")
