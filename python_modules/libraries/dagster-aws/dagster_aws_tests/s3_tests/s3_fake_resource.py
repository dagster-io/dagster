from collections import defaultdict
import io

from dagster_aws.s3.resources import S3Resource


def create_s3_fake_resource():
    return S3Resource(S3FakeSession())


class S3FakeSession:
    def __init__(self):
        self.buckets = defaultdict(dict)

    def head_bucket(self, Bucket, *_args, **_kwargs):
        pass

    def head_object(self, Bucket, Key, *_args, **_kwargs):
        return {'ContentLength': len(self.buckets.get(Bucket, {}).get(Key, b''))}

    def list_objects_v2(self, Bucket, Prefix, *_args, **_kwargs):
        key = self.buckets.get(Bucket, {}).get(Prefix)
        if key:
            return {'KeyCount': 1, 'Contents': [{'Key': key}], 'IsTruncated': False}
        else:
            return {'KeyCount': 0, 'Contents': [], 'IsTruncated': False}

    def put_object(self, Bucket, Key, Body, *_args, **_kwargs):
        self.buckets[Bucket][Key] = Body.read()

    def get_object(self, Bucket, Key, *_args, **_kwargs):
        return {'Body': self._get_byte_stream(Bucket, Key)}

    def _get_byte_stream(self, bucket, key):
        return io.BytesIO(self.buckets[bucket][key])

    def download_file(self, Bucket, Key, Filename, *_args, **_kwargs):
        with open(Filename, 'wb') as ff:
            ff.write(self._get_byte_stream(Bucket, Key).read())
