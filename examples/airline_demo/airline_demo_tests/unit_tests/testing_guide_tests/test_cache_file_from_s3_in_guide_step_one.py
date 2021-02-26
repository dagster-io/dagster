import os
import shutil
from unittest import mock

import boto3
from dagster import execute_pipeline, pipeline, solid
from dagster.utils.temp_file import get_temp_dir, get_temp_file_name
from dagster.utils.test import execute_solid
from dagster_aws.s3 import S3Coordinate


def file_cache_folder():
    return "file_cache"


@solid
def cache_file_from_s3(_, s3_coord: S3Coordinate) -> str:
    # we default the target_key to the last component of the s3 key.
    target_key = s3_coord["key"].split("/")[-1]

    with get_temp_file_name() as tmp_file:
        boto3.client("s3").download_file(
            Bucket=s3_coord["bucket"], Key=s3_coord["key"], Filename=tmp_file
        )

        target_path = os.path.join(file_cache_folder(), target_key)
        with open(tmp_file, "rb") as tmp_file_object:
            with open(target_path, "wb") as target_file_object:
                shutil.copyfileobj(tmp_file_object, target_file_object)
                return target_path


def test_cache_file_from_s3_step_one_one():
    boto_s3 = mock.MagicMock()
    # mock.patch is difficult to get right and requires monkeypatching of global artifacts
    with get_temp_dir() as temp_dir, mock.patch(
        file_cache_folder.__module__ + ".file_cache_folder", new=lambda: temp_dir
    ), mock.patch("boto3.client", new=lambda *_args, **_kwargs: boto_s3):

        @solid
        def emit_value(_):
            return {"bucket": "some-bucket", "key": "some-key"}

        @pipeline
        def pipe():

            return cache_file_from_s3(emit_value())

        execute_pipeline(pipe)

        assert boto_s3.download_file.call_count == 1

        assert os.path.exists(os.path.join(temp_dir, "some-key"))


def test_cache_file_from_s3_step_one_two():
    boto_s3 = mock.MagicMock()
    # mock.patch is difficult to get right and requires monkeypatching of global artifacts
    with get_temp_dir() as temp_dir, mock.patch(
        file_cache_folder.__module__ + ".file_cache_folder", new=lambda: temp_dir
    ), mock.patch("boto3.client", new=lambda *_args, **_kwargs: boto_s3):
        execute_solid(
            cache_file_from_s3,
            input_values=dict(s3_coord={"bucket": "some-bucket", "key": "some-key"}),
        )

        assert boto_s3.download_file.call_count == 1

        assert os.path.exists(os.path.join(temp_dir, "some-key"))
