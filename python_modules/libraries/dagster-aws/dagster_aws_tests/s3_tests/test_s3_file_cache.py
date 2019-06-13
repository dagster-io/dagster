import io

from dagster_aws.s3.file_cache import S3FileCache, S3FileHandle
from dagster_aws.s3.s3_fake_resource import S3FakeSession


def test_s3_file_cache_file_not_present():
    session_fake = S3FakeSession()
    file_store = S3FileCache(
        s3_bucket='some-bucket', s3_key='some-key', s3_session=session_fake, overwrite=False
    )

    assert not file_store.has_file_object('foo')


def test_s3_file_cache_file_present():
    session_fake = S3FakeSession()
    file_store = S3FileCache(
        s3_bucket='some-bucket', s3_key='some-key', s3_session=session_fake, overwrite=False
    )

    assert not file_store.has_file_object('foo')

    file_store.write_binary_data('foo', 'bar'.encode())

    assert file_store.has_file_object('foo')


def test_s3_file_cache_correct_handle():
    session_fake = S3FakeSession()
    file_store = S3FileCache(
        s3_bucket='some-bucket', s3_key='some-key', s3_session=session_fake, overwrite=False
    )

    assert isinstance(file_store.get_file_handle('foo'), S3FileHandle)


def test_s3_file_cache_write_file_object():
    session_fake = S3FakeSession()
    file_store = S3FileCache(
        s3_bucket='some-bucket', s3_key='some-key', s3_session=session_fake, overwrite=False
    )

    stream = io.BytesIO('content'.encode())
    file_store.write_file_object('foo', stream)
