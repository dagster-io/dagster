import os

import boto3

from dagster import solid, Bool, Dict, Field, OutputDefinition, Path, String
from dagster.utils import safe_isfile, mkdir_p

from .types import FileExistsAtPath


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
            'Download of {bucket}/{key} to {target_file}: {percentage:.2f}% complete'.format(
                bucket=self._bucket,
                key=self._key,
                target_file=self._filename,
                percentage=percentage,
            )
        )


@solid(
    name='download_from_s3',
    config_field=Field(
        Dict(
            fields={
                'bucket': Field(String),
                'key': Field(String),
                'target_folder': Field(
                    Path, description=('Specifies the path at which to download the object.')
                ),
                'skip_if_present': Field(Bool, is_optional=True, default_value=False),
            }
        )
    ),
    description='Downloads an object from S3.',
    outputs=[OutputDefinition(FileExistsAtPath, description='The path to the downloaded object.')],
)
def download_from_s3(context):
    (bucket, key, target_folder, skip_if_present) = (
        context.solid_config.get(k) for k in ('bucket', 'key', 'target_folder', 'skip_if_present')
    )

    # file name is S3 key path suffix after last /
    target_file = os.path.join(target_folder, key.split('/')[-1])

    if skip_if_present and safe_isfile(target_file):
        context.log.info(
            'Skipping download, file already present at {target_file}'.format(
                target_file=target_file
            )
        )
    else:
        if not os.path.exists(target_folder):
            mkdir_p(target_folder)

        context.log.info(
            'Starting download of {bucket}/{key} to {target_file}'.format(
                bucket=bucket, key=key, target_file=target_file
            )
        )
        s3 = boto3.client('s3')

        headers = s3.head_object(Bucket=bucket, Key=key)
        logger = S3Logger(
            context.log.debug, bucket, key, target_file, int(headers['ContentLength'])
        )
        s3.download_file(Bucket=bucket, Key=key, Filename=target_file, Callback=logger)

    return target_file
