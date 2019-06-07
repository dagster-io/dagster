from abc import ABCMeta, abstractmethod, abstractproperty
import io
import os
import shutil

import six

from dagster import check, resource, Bool, Field, String, Dict, dagster_type
from dagster.utils import mkdir_p
from dagster_aws.s3.utils import create_s3_session
from botocore.exceptions import ClientError


@dagster_type  # pylint: disable=no-init
class FileHandle(six.with_metaclass(ABCMeta)):
    @abstractproperty
    def path_desc(self):
        pass


class LocalFileHandle(FileHandle):
    def __init__(self, path):
        self._path = check.str_param(path, 'path')

    @property
    def path_desc(self):
        return self._path


class S3FileHandle(FileHandle):
    def __init__(self, s3_bucket, s3_key):
        self.s3_bucket = check.str_param(s3_bucket, 's3_bucket')
        self.s3_key = check.str_param(s3_key, 's3_key')

    @property
    def path_desc(self):
        return 's3://{bucket}/{key}'.format(bucket=self.s3_bucket, key=self.s3_key)


class KeyedFileStore(six.with_metaclass(ABCMeta)):
    def __init__(self, overwrite):
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


class KeyedFilesystemFileStore(KeyedFileStore):
    def __init__(self, target_folder, overwrite=False):
        super(KeyedFilesystemFileStore, self).__init__(overwrite=overwrite)
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
def keyed_fs_file_store(init_context):
    target_folder = init_context.resource_config['target_folder']

    if not os.path.exists(target_folder):
        mkdir_p(target_folder)

    return KeyedFilesystemFileStore(target_folder=target_folder, overwrite=False)


class KeyedS3FileStore(KeyedFileStore):
    def __init__(self, s3_bucket, s3_key, s3_session, overwrite=False):
        super(KeyedS3FileStore, self).__init__(overwrite=overwrite)

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
def keyed_s3_file_store(init_context):
    return KeyedS3FileStore(
        s3_bucket=init_context.resource_config['bucket'],
        s3_key=init_context.resource_config['key'],
        overwrite=init_context.resource_config['overwrite'],
        s3_session=create_s3_session(),
    )
