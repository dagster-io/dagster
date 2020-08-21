import os
import shutil
import tempfile

from dagster_examples.bay_bikes.resources import LocalBlob, LocalBucket, LocalClient

from dagster import seven


def test_local_blob_upload():
    with seven.TemporaryDirectory() as bucket_dir:
        target_key = os.path.join(bucket_dir, "foo.txt")
        # TODO: Make this windows safe
        with tempfile.NamedTemporaryFile() as local_fp:
            blob = LocalBlob("foo.txt", bucket_dir)
            local_fp.write(b"hello")
            local_fp.seek(0)
            blob.upload_from_file(local_fp)
        assert os.path.exists(target_key)
        with open(target_key) as key_fp:
            assert key_fp.read() == "hello"


def test_local_bucket():
    bucket = LocalBucket("foo", "mountain")
    assert os.path.exists(os.path.join(tempfile.gettempdir(), "mountain", "foo"))

    bucket.blob("bar.txt")
    assert isinstance(bucket.blobs["bar.txt"], LocalBlob)
    assert bucket.blobs["bar.txt"].key == "bar.txt"
    assert bucket.blobs["bar.txt"].location == os.path.join(
        tempfile.gettempdir(), "mountain", "foo", "bar.txt"
    )
    shutil.rmtree(os.path.join(tempfile.gettempdir(), "mountain"), ignore_errors=True)


def test_local_client():
    client = LocalClient(volume="mountain")
    client.get_bucket("foo")
    assert isinstance(client.buckets["foo"], LocalBucket)
    assert client.buckets["foo"].bucket_name == "foo"
    assert client.buckets["foo"].volume == os.path.join(tempfile.gettempdir(), "mountain")
    shutil.rmtree(os.path.join(tempfile.gettempdir(), "mountain"), ignore_errors=True)
