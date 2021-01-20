import io

from dagster_aws.s3 import S3FileCache, S3FileHandle


def test_s3_file_cache_file_not_present(mock_s3_resource, mock_s3_bucket):
    file_store = S3FileCache(
        s3_bucket=mock_s3_bucket.name,
        s3_key="some-key",
        s3_session=mock_s3_resource.meta.client,
        overwrite=False,
    )

    assert not file_store.has_file_object("foo")


def test_s3_file_cache_file_present(mock_s3_resource, mock_s3_bucket):
    file_store = S3FileCache(
        s3_bucket=mock_s3_bucket.name,
        s3_key="some-key",
        s3_session=mock_s3_resource.meta.client,
        overwrite=False,
    )

    assert not file_store.has_file_object("foo")

    file_store.write_binary_data("foo", b"bar")

    assert file_store.has_file_object("foo")


def test_s3_file_cache_correct_handle(mock_s3_resource, mock_s3_bucket):
    file_store = S3FileCache(
        s3_bucket=mock_s3_bucket.name,
        s3_key="some-key",
        s3_session=mock_s3_resource.meta.client,
        overwrite=False,
    )

    assert isinstance(file_store.get_file_handle("foo"), S3FileHandle)


def test_s3_file_cache_write_file_object(mock_s3_resource, mock_s3_bucket):
    file_store = S3FileCache(
        s3_bucket=mock_s3_bucket.name,
        s3_key="some-key",
        s3_session=mock_s3_resource.meta.client,
        overwrite=False,
    )

    stream = io.BytesIO(b"content")
    file_store.write_file_object("foo", stream)
