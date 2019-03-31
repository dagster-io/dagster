import os

import boto3

from dagster import Field, resource, check, Dict, String, Path, Bool
from dagster.utils import safe_isfile, mkdir_p


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


class S3DownloadManager:
    def __init__(self, bucket, key, target_folder, skip_if_present):
        self.bucket = check.str_param(bucket, 'bucket')
        self.key = check.str_param(key, 'key')
        self.target_folder = check.str_param(target_folder, 'target_folder')
        self.skip_if_present = check.bool_param(skip_if_present, 'skip_if_present')

    def download_file(self, context, target_file):
        check.str_param(target_file, 'target_file')

        target_path = os.path.join(self.target_folder, target_file)

        if self.skip_if_present and safe_isfile(target_path):
            context.log.info(
                'Skipping download, file already present at {target_path}'.format(
                    target_path=target_path
                )
            )
        else:
            full_key = self.key + '/' + target_file
            if os.path.dirname(target_path):
                mkdir_p(os.path.dirname(target_path))

            context.log.info(
                'Starting download of {bucket}/{key} to {target_path}'.format(
                    bucket=self.bucket, key=full_key, target_path=target_path
                )
            )

            headers = context.resources.s3.head_object(Bucket=self.bucket, Key=full_key)
            logger = S3Logger(
                context.log.debug, self.bucket, full_key, target_path, int(headers['ContentLength'])
            )
            context.resources.s3.download_file(
                Bucket=self.bucket, Key=full_key, Filename=target_path, Callback=logger
            )

        return target_path


@resource(
    config_field=Field(
        Dict(
            {
                'bucket': Field(String),
                'key': Field(String),
                'target_folder': Field(Path),
                'skip_if_present': Field(Bool),
            }
        )
    )
)
def s3_download_manager(init_context):
    return S3DownloadManager(
        bucket=init_context.resource_config['bucket'],
        key=init_context.resource_config['key'],
        target_folder=init_context.resource_config['target_folder'],
        skip_if_present=init_context.resource_config['skip_if_present'],
    )


@resource
def unsigned_s3_session(_init_context):
    s3 = boto3.resource('s3').meta.client  # pylint:disable=C0103
    if not signed:
        s3.meta.events.register('choose-signer.s3.*', disable_signing)
    return s3
