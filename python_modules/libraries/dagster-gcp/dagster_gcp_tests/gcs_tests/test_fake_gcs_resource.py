from dagster_gcp.gcs import FakeGCSBlob, FakeGCSBucket, FakeGCSClient


def test_fake_blob_read_write():
    bucket = FakeGCSBucket("my_bucket")
    blob = FakeGCSBlob("my_blob", bucket)

    assert blob.exists()

    my_string = "this is a unit test"
    blob.upload_from_string(my_string)
    assert blob.download_as_bytes() == my_string.encode()

    my_bytes = b"these are some bytes"
    blob.upload_from_string(my_bytes)
    assert blob.download_as_bytes() == my_bytes


def test_blob_delete():
    bucket = FakeGCSBucket("my_bucket")
    foo = bucket.blob("foo")
    bar = bucket.blob("bar")

    foo.upload_from_string("foo")
    bar.upload_from_string("bar")

    assert "foo" in bucket.blobs.keys()
    assert "bar" in bucket.blobs.keys()

    foo.delete()

    assert "foo" not in bucket.blobs.keys()
    assert "bar" in bucket.blobs.keys()

    bar.delete()

    assert "bar" not in bucket.blobs.keys()


def test_bucket():
    bucket = FakeGCSBucket("my_bucket")

    assert bucket.exists()

    foo = bucket.blob("foo")
    bar = bucket.blob("bar")

    assert bucket.blob("foo") == foo
    assert bucket.blob("bar") == bar


def test_client_blobs():
    client = FakeGCSClient()

    foo = client.bucket("foo")
    assert client.bucket("foo") == foo

    bar = foo.blob("bar")
    assert [bar] == list(client.list_blobs("foo"))

    baz = foo.blob("baz/aaa")
    assert [bar, baz] == list(client.list_blobs("foo"))

    assert [baz] == list(client.list_blobs("foo", prefix="baz"))
    assert [] == list(client.list_blobs("foo", prefix="xyz"))


def test_client_bucekts():
    client = FakeGCSClient()

    foo = client.bucket("foo")
    bar = client.bucket("bar")

    assert [foo, bar] == list(client.list_buckets())
