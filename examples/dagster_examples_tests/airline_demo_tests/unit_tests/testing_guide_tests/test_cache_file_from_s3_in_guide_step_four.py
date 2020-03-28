# https://github.com/dagster-io/dagster/issues/2326 Change import after next release to PyPI
from dagster_aws.s3.file_cache import S3FileCache
from dagster_aws.s3.s3_fake_resource import S3FakeSession
from dagster_aws.s3.solids import S3Coordinate

from dagster import FileHandle, ModeDefinition, solid
from dagster.utils.temp_file import get_temp_file_name
from dagster.utils.test import execute_solid


@solid(required_resource_keys={'file_cache', 's3'})
def cache_file_from_s3(context, s3_coord: S3Coordinate) -> FileHandle:
    # we default the target_key to the last component of the s3 key.
    target_key = s3_coord['key'].split('/')[-1]

    with get_temp_file_name() as tmp_file:
        # https://github.com/dagster-io/dagster/issues/2326 Remove .session on next PyPI release
        context.resources.s3.session.download_file(
            Bucket=s3_coord['bucket'], Key=s3_coord['key'], Filename=tmp_file
        )

        file_cache = context.resources.file_cache
        with open(tmp_file, 'rb') as tmp_file_object:
            # returns a handle rather than a path
            file_handle = file_cache.write_file_object(target_key, tmp_file_object)
            return file_handle


def unittest_for_aws_mode_def(s3_file_cache_session, s3_session):
    return ModeDefinition.from_resources(
        {
            'file_cache': S3FileCache('file-cache-bucket', 'file-cache', s3_file_cache_session),
            's3': s3_session,
        }
    )


def test_cache_file_from_s3_step_four(snapshot):
    s3_session = S3FakeSession({'source-bucket': {'source-file': b'foo'}})
    s3_file_cache_session = S3FakeSession()

    solid_result = execute_solid(
        cache_file_from_s3,
        unittest_for_aws_mode_def(s3_file_cache_session, s3_session),
        input_values={'s3_coord': {'bucket': 'source-bucket', 'key': 'source-file'}},
    )

    assert solid_result.output_value().path_desc == 's3://file-cache-bucket/file-cache/source-file'

    file_cache_obj = s3_file_cache_session.get_object(
        Bucket='file-cache-bucket', Key='file-cache/source-file'
    )

    assert file_cache_obj['Body'].read() == b'foo'

    # just perform a snapshot of the bucket structure as well
    snapshot.assert_match(s3_file_cache_session.buckets)
