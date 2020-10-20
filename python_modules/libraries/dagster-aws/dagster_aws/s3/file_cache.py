import boto3
from botocore.exceptions import ClientError
from dagster import Field, check, resource
from dagster.core.storage.file_cache import FileCache

from .file_manager import S3FileHandle


class S3FileCache(FileCache):
    def __init__(self, s3_bucket, s3_key, s3_session, overwrite=False):
        super(S3FileCache, self).__init__(overwrite=overwrite)

        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.s3 = s3_session

    def has_file_object(self, file_key):
        check.str_param(file_key, "file_key")
        try:
            self.s3.get_object(Bucket=self.s3_bucket, Key=self.get_full_key(file_key))
        except ClientError:
            return False
        return True

    def get_full_key(self, file_key):
        return "{base_key}/{file_key}".format(base_key=self.s3_key, file_key=file_key)

    def write_file_object(self, file_key, source_file_object):
        check.str_param(file_key, "file_key")

        self.s3.put_object(
            Body=source_file_object, Bucket=self.s3_bucket, Key=self.get_full_key(file_key)
        )
        return self.get_file_handle(file_key)

    def get_file_handle(self, file_key):
        check.str_param(file_key, "file_key")
        return S3FileHandle(self.s3_bucket, self.get_full_key(file_key))


@resource(
    {
        "bucket": Field(str),
        "key": Field(str),
        "overwrite": Field(bool, is_required=False, default_value=False),
    }
)
def s3_file_cache(init_context):
    return S3FileCache(
        s3_bucket=init_context.resource_config["bucket"],
        s3_key=init_context.resource_config["key"],
        overwrite=init_context.resource_config["overwrite"],
        # TODO: resource dependencies
        s3_session=boto3.resource("s3", use_ssl=True).meta.client,
    )
