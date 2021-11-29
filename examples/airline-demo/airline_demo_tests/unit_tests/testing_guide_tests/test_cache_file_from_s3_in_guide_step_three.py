import os
from unittest import mock

import boto3
from dagster import ModeDefinition, solid
from dagster.core.storage.file_cache import FSFileCache
from dagster.utils.temp_file import get_temp_dir, get_temp_file_name
from dagster.utils.test import execute_solid
from dagster_aws.s3 import S3Coordinate
from moto import mock_s3


@solid(required_resource_keys={"file_cache", "s3"})
def cache_file_from_s3(context, s3_coord: S3Coordinate) -> str:
    # we default the target_key to the last component of the s3 key.
    target_key = s3_coord["key"].split("/")[-1]

    with get_temp_file_name() as tmp_file:
        context.resources.s3.download_file(
            Bucket=s3_coord["bucket"], Key=s3_coord["key"], Filename=tmp_file
        )

        file_cache = context.resources.file_cache
        with open(tmp_file, "rb") as tmp_file_object:
            # returns a handle rather than a path
            file_handle = file_cache.write_file_object(target_key, tmp_file_object)
            return file_handle.path


def unittest_for_local_mode_def(temp_dir, s3_session):
    return ModeDefinition.from_resources({"file_cache": FSFileCache(temp_dir), "s3": s3_session})


def test_cache_file_from_s3_step_three_mock():
    s3_session = mock.MagicMock()
    with get_temp_dir() as temp_dir:
        execute_solid(
            cache_file_from_s3,
            unittest_for_local_mode_def(temp_dir, s3_session),
            input_values={"s3_coord": {"bucket": "some-bucket", "key": "some-key"}},
        )

        assert s3_session.download_file.call_count == 1

        assert os.path.exists(os.path.join(temp_dir, "some-key"))


@mock_s3
def test_cache_file_from_s3_step_three_fake(snapshot):
    # https://github.com/spulec/moto/issues/3292
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="some-bucket")
    s3.put_object(Bucket="some-bucket", Key="some-key", Body=b"foo")

    with get_temp_dir() as temp_dir:
        execute_solid(
            cache_file_from_s3,
            unittest_for_local_mode_def(temp_dir, s3),
            input_values={"s3_coord": {"bucket": "some-bucket", "key": "some-key"}},
        )

        target_file = os.path.join(temp_dir, "some-key")
        assert os.path.exists(target_file)

        with open(target_file, "rb") as ff:
            assert ff.read() == b"foo"

    snapshot.assert_match(
        {
            "some-bucket": {
                k: s3.get_object(Bucket="some-bucket", Key=k)["Body"].read()
                for k in [obj["Key"] for obj in s3.list_objects(Bucket="some-bucket")["Contents"]]
            }
        }
    )
