import os

# https://github.com/dagster-io/dagster/issues/2326 Change import after next release to PyPI
from dagster_aws.s3.s3_fake_resource import S3FakeSession
from dagster_aws.s3.solids import S3Coordinate

from dagster import ModeDefinition, solid
from dagster.core.storage.file_cache import FSFileCache
from dagster.seven import mock
from dagster.utils.temp_file import get_temp_dir, get_temp_file_name
from dagster.utils.test import execute_solid


@solid(required_resource_keys={'file_cache', 's3'})
def cache_file_from_s3(context, s3_coord: S3Coordinate) -> str:
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
            return file_handle.path


def unittest_for_local_mode_def(temp_dir, s3_session):
    return ModeDefinition.from_resources({'file_cache': FSFileCache(temp_dir), 's3': s3_session})


def test_cache_file_from_s3_step_three_mock():
    s3_session = mock.MagicMock()
    with get_temp_dir() as temp_dir:
        execute_solid(
            cache_file_from_s3,
            unittest_for_local_mode_def(temp_dir, s3_session),
            input_values={'s3_coord': {'bucket': 'some-bucket', 'key': 'some-key'}},
        )

        # https://github.com/dagster-io/dagster/issues/2326 Remove .session on next PyPI release
        assert s3_session.session.download_file.call_count == 1

        assert os.path.exists(os.path.join(temp_dir, 'some-key'))


def test_cache_file_from_s3_step_three_fake(snapshot):
    s3_session = S3FakeSession({'some-bucket': {'some-key': b'foo'}})

    with get_temp_dir() as temp_dir:
        execute_solid(
            cache_file_from_s3,
            unittest_for_local_mode_def(temp_dir, s3_session),
            input_values={'s3_coord': {'bucket': 'some-bucket', 'key': 'some-key'}},
        )

        target_file = os.path.join(temp_dir, 'some-key')
        assert os.path.exists(target_file)

        with open(target_file, 'rb') as ff:
            assert ff.read() == b'foo'

        snapshot.assert_match(s3_session.buckets)
