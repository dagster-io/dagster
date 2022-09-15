import io
from collections import defaultdict

from botocore.exceptions import ClientError


def create_s3_fake_resource(buckets=None):
    """Create a mock S3 session for test."""
    return S3FakeSession(buckets=buckets)


class S3FakeSession:
    """Stateful mock of a boto3 s3 session for test.

    Wraps a ``mock.MagicMock``. Buckets are implemented using an in-memory dict.
    """

    def __init__(self, buckets=None):
        from unittest import mock

        self.buckets = defaultdict(dict, buckets) if buckets else defaultdict(dict)
        self.mock_extras = mock.MagicMock()

    def head_bucket(self, Bucket, *args, **kwargs):  # pylint: disable=unused-argument
        self.mock_extras.head_bucket(*args, **kwargs)

    def head_object(self, Bucket, Key, *args, **kwargs):
        self.mock_extras.head_object(*args, **kwargs)
        return {"ContentLength": len(self.buckets.get(Bucket, {}).get(Key, b""))}

    def _list_objects(self, Bucket, Prefix):
        key = self.buckets.get(Bucket, {}).get(Prefix)
        if key:
            return {"KeyCount": 1, "Contents": [{"Key": key}], "IsTruncated": False}
        else:
            return {"KeyCount": 0, "Contents": [], "IsTruncated": False}

    def list_objects_v2(self, Bucket, Prefix, *args, **kwargs):
        self.mock_extras.list_objects_v2(*args, **kwargs)
        return self._list_objects(Bucket, Prefix)

    def list_objects(self, Bucket, Prefix, *args, **kwargs):
        self.mock_extras.list_objects(*args, **kwargs)
        return self._list_objects(Bucket, Prefix)

    def put_object(self, Bucket, Key, Body, *args, **kwargs):
        self.mock_extras.put_object(*args, **kwargs)
        self.buckets[Bucket][Key] = Body.read()

    def get_object(self, Bucket, Key, *args, **kwargs):
        if not self.has_object(Bucket, Key):
            raise ClientError({}, None)

        self.mock_extras.get_object(*args, **kwargs)
        return {"Body": self._get_byte_stream(Bucket, Key)}

    def upload_fileobj(self, fileobj, bucket, key, *args, **kwargs):
        self.mock_extras.upload_fileobj(*args, **kwargs)
        self.buckets[bucket][key] = fileobj.read()

    def has_object(self, bucket, key):
        return bucket in self.buckets and key in self.buckets[bucket]

    def _get_byte_stream(self, bucket, key):
        return io.BytesIO(self.buckets[bucket][key])

    def download_file(self, Bucket, Key, Filename, *args, **kwargs):
        self.mock_extras.download_file(*args, **kwargs)
        with open(Filename, "wb") as ff:
            ff.write(self._get_byte_stream(Bucket, Key).read())
