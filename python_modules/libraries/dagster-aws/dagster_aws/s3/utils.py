import boto3

from botocore.handlers import disable_signing


def create_s3_session(signed=True):
    s3 = boto3.resource('s3').meta.client  # pylint:disable=C0103
    if not signed:
        s3.meta.events.register('choose-signer.s3.*', disable_signing)
    return s3


class S3Logger(object):
    def __init__(self, logger, bucket, key, filename, size):
        self._logger = logger
        self._bucket = bucket
        self._key = key
        self._filename = filename
        self._seen_so_far = 0
        self._size = size

    def __call__(self, bytes_amount):
        self._seen_so_far += bytes_amount
        percentage = (self._seen_so_far / self._size) * 100
        self._logger(
            'Download of {bucket}/{key} to {target_path}: {percentage}% complete'.format(
                bucket=self._bucket,
                key=self._key,
                target_path=self._filename,
                percentage=percentage,
            )
        )
