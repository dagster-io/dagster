import boto3
from dagster_aws.s3 import S3Coordinate, S3FileCache
from moto import mock_s3

from dagster import FileHandle, ModeDefinition, solid
from dagster.utils.temp_file import get_temp_file_name
from dagster.utils.test import execute_solid


@solid(required_resource_keys={"file_cache", "s3"})
def cache_file_from_s3(context, s3_coord: S3Coordinate) -> FileHandle:
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
            return file_handle


def unittest_for_aws_mode_def(s3_session):
    return ModeDefinition.from_resources(
        {
            "file_cache": S3FileCache("file-cache-bucket", "file-cache", s3_session),
            "s3": s3_session,
        }
    )


@mock_s3
def test_cache_file_from_s3_step_four(snapshot):
    # https://github.com/spulec/moto/issues/3292
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="source-bucket")
    s3.create_bucket(Bucket="file-cache-bucket")
    s3.put_object(Bucket="source-bucket", Key="source-file", Body=b"foo")

    solid_result = execute_solid(
        cache_file_from_s3,
        unittest_for_aws_mode_def(s3),
        input_values={"s3_coord": {"bucket": "source-bucket", "key": "source-file"}},
    )

    assert solid_result.output_value().path_desc == "s3://file-cache-bucket/file-cache/source-file"

    file_cache_obj = s3.get_object(Bucket="file-cache-bucket", Key="file-cache/source-file")

    assert file_cache_obj["Body"].read() == b"foo"

    snapshot.assert_match(
        {
            "file-cache-bucket": {
                k: s3.get_object(Bucket="file-cache-bucket", Key=k)["Body"].read()
                for k in [
                    obj["Key"] for obj in s3.list_objects(Bucket="file-cache-bucket")["Contents"]
                ]
            }
        }
    )
