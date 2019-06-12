from abc import ABCMeta, abstractmethod
import io
import os
import shutil

import six

from dagster import check, resource, Bool, Field, String, Dict
from dagster.core.storage.file_manager import LocalFileHandle
from dagster.utils import mkdir_p
from dagster_aws.s3.file_manager import S3FileHandle
from dagster_aws.s3.utils import create_s3_session
from botocore.exceptions import ClientError


class FileCache(six.with_metaclass(ABCMeta)):
    def __init__(self, overwrite):
        # Overwrite is currently only a signal to callers to not overwrite.
        # These classes currently do not enforce any semantics around that
        self.overwrite = check.bool_param(overwrite, 'overwrite')

    @abstractmethod
    def has_file_object(self, file_key):
        pass

    @abstractmethod
    def get_file_handle(self, file_key):
        pass

    @abstractmethod
    def write_file_object(self, file_key, source_file_object):
        pass

    def write_binary_data(self, file_key, binary_data):
        return self.write_file_object(file_key, io.BytesIO(binary_data))


class FSFileCache(FileCache):
    def __init__(self, target_folder, overwrite=False):
        super(FSFileCache, self).__init__(overwrite=overwrite)
        check.str_param(target_folder, 'target_folder')
        check.param_invariant(os.path.isdir(target_folder), 'target_folder')

        self.target_folder = target_folder

    def has_file_object(self, file_key):
        return os.path.exists(self.get_full_path(file_key))

    def write_file_object(self, file_key, source_file_object):
        target_file = self.get_full_path(file_key)
        with open(target_file, 'wb') as dest_file_object:
            shutil.copyfileobj(source_file_object, dest_file_object)
        return LocalFileHandle(target_file)

    def get_file_handle(self, file_key):
        check.str_param(file_key, 'file_key')
        return LocalFileHandle(self.get_full_path(file_key))

    def get_full_path(self, file_key):
        check.str_param(file_key, 'file_key')
        return os.path.join(self.target_folder, file_key)


@resource(
    config_field=Field(
        Dict(
            {
                'overwrite': Field(Bool, is_optional=True, default_value=False),
                'target_folder': Field(String),
            }
        )
    )
)
def fs_file_cache(init_context):
    target_folder = init_context.resource_config['target_folder']

    if not os.path.exists(target_folder):
        mkdir_p(target_folder)

    return FSFileCache(target_folder=target_folder, overwrite=False)


class S3FileCache(FileCache):
    def __init__(self, s3_bucket, s3_key, s3_session, overwrite=False):
        super(S3FileCache, self).__init__(overwrite=overwrite)

        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.s3 = s3_session

    def has_file_object(self, file_key):
        check.str_param(file_key, 'file_key')
        try:
            self.s3.get_object(Bucket=self.s3_bucket, Key=self.get_full_key(file_key))
        except ClientError:
            return False
        return True

    def get_full_key(self, file_key):
        return '{base_key}/{file_key}'.format(base_key=self.s3_key, file_key=file_key)

    def write_file_object(self, file_key, source_file_object):
        check.str_param(file_key, 'file_key')

        self.s3.put_object(
            Body=source_file_object, Bucket=self.s3_bucket, Key=self.get_full_key(file_key)
        )

    def get_file_handle(self, file_key):
        check.str_param(file_key, 'file_key')
        return S3FileHandle(self.s3_bucket, self.get_full_key(file_key))


@resource(
    config_field=Field(
        Dict(
            {
                'bucket': Field(String),
                'key': Field(String),
                'overwrite': Field(Bool, is_optional=True, default_value=False),
            }
        )
    )
)
def s3_file_cache(init_context):
    return S3FileCache(
        s3_bucket=init_context.resource_config['bucket'],
        s3_key=init_context.resource_config['key'],
        overwrite=init_context.resource_config['overwrite'],
        # TODO: resource dependencies
        s3_session=create_s3_session(),
    )
