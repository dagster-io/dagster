from typing import AbstractSet, Optional, Union  # noqa: UP035

from dagster._utils.cached_method import cached_method


class FakeGCSBlob:
    def __init__(self, name: str, bucket: "FakeGCSBucket"):
        from unittest import mock

        self.name = name
        self.data = b""
        self.bucket = bucket
        self.mock_extras = mock.MagicMock()

    def exists(self, *args, **kwargs):
        self.mock_extras.exists(*args, **kwargs)
        return True

    def delete(self, *args, **kwargs):
        self.mock_extras.delete(*args, **kwargs)
        del self.bucket.blobs[self.name]

    def download_as_bytes(self, *args, **kwargs):
        self.mock_extras.download_as_bytes(*args, **kwargs)
        return self.data

    def upload_from_string(self, data: Union[bytes, str], *args, **kwargs):
        self.mock_extras.upload_from_string(*args, **kwargs)
        if isinstance(data, str):
            self.data = data.encode()
        else:
            self.data = data


class FakeGCSBucket:
    def __init__(self, name: str):
        from unittest import mock

        self.name = name
        self.blobs: dict[str, FakeGCSBlob] = {}
        self.mock_extras = mock.MagicMock()

    def blob(self, blob_name: str, *args, **kwargs):
        self.mock_extras.blob(*args, **kwargs)

        if blob_name not in self.blobs.keys():
            self.blobs[blob_name] = FakeGCSBlob(name=blob_name, bucket=self)

        return self.blobs[blob_name]

    def exists(self, *args, **kwargs):
        self.mock_extras.exists(*args, **kwargs)
        return True


class FakeGCSClient:
    def __init__(self):
        from unittest import mock

        self.buckets: dict[str, FakeGCSBucket] = {}
        self.mock_extras = mock.MagicMock()

    def bucket(self, bucket_name: str, *args, **kwargs):
        self.mock_extras.bucket(*args, **kwargs)

        if bucket_name not in self.buckets.keys():
            self.buckets[bucket_name] = FakeGCSBucket(name=bucket_name)

        return self.buckets[bucket_name]

    def list_buckets(self, *args, **kwargs):
        self.mock_extras.list_buckets(*args, **kwargs)
        yield from self.buckets.values()

    def list_blobs(
        self,
        bucket_or_name: Union[FakeGCSBucket, str],
        *args,
        prefix: Optional[str] = None,
        **kwargs,
    ):
        self.mock_extras.list_blobs(*args, **kwargs)

        if isinstance(bucket_or_name, str):
            bucket = self.bucket(bucket_or_name)
        else:
            bucket = bucket_or_name

        for blob in self.buckets[bucket.name].blobs.values():
            if prefix is None:
                yield blob
            elif prefix in blob.name:
                yield blob

    def get_all_blob_paths(self) -> AbstractSet[str]:
        return {
            f"{bucket.name}/{blob.name}"
            for bucket in self.buckets.values()
            for blob in bucket.blobs.values()
        }


class FakeConfigurableGCSClient:
    @cached_method
    def get_client(self):
        return FakeGCSClient()
