import os

from dagster import Field, resource, Dict, Bool
from dagster.utils import safe_isfile, mkdir_p

from .utils import create_s3_session, S3Logger


class S3Resource:
    def __init__(self, use_unsigned_session=True):
        self.s3 = create_s3_session(signed=(not use_unsigned_session))

    def download_from_s3_to_bytes(self, bucket, key):
        return self.s3.get_object(Bucket=bucket, Key=key)['Body'].read()

    def download_from_s3_to_file(self, context, bucket, key, target_folder, skip_if_present):
        # TODO: remove context argument once we support resource logging

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

            headers = self.s3.head_object(Bucket=bucket, Key=key)
            logger = S3Logger(
                context.log.debug, bucket, key, target_file, int(headers['ContentLength'])
            )
            self.s3.download_file(Bucket=bucket, Key=key, Filename=target_file, Callback=logger)
        return target_file

    def put_object(self, **kwargs):
        '''This mirrors the put_object boto3 API:
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#S3.Bucket.put_object

        The config schema for this API is applied to the put_object_to_s3_bytes solid vs. at the
        resource level here.
        '''
        return self.s3.put_object(**kwargs)


@resource(
    config_field=Field(
        Dict(
            {
                'use_unsigned_session': Field(
                    Bool,
                    description='Specifies whether to use an unsigned S3 session',
                    is_optional=True,
                    default_value=True,
                )
            }
        )
    )
)
def s3_resource(context):
    return S3Resource(use_unsigned_session=context.resource_config['use_unsigned_session'])
