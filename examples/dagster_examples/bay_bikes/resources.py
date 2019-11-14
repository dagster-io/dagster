import json
import os
from abc import ABCMeta, abstractmethod

from google.cloud import storage
from google.cloud.exceptions import NotFound
from six import with_metaclass

from dagster import Field, String, check, resource, seven


class DagsterCloudResourceSDKException(Exception):
    def __init__(self, inner_error):
        check.inst_param(inner_error, 'inner_error', Exception)
        self.inner_error = inner_error
        message = ('Recevied error of type {}. Reason: {}.', format(type(inner_error), inner_error))
        super(DagsterCloudResourceSDKException, self).__init__(message)


class AbstractFileTransporter(with_metaclass(ABCMeta)):
    """
    This is a class that moves data between your filesystem and an existing bucket on a cloud platform.

    The logic for doing so is left to the child classes which implement this interface for their respective
    cloud platforms.

    TODO: Implement the download logic once you need this functionality.
    """

    @abstractmethod
    def upload_file_to_bucket(self, path_to_file, key):
        pass

    @staticmethod
    def path_to_file_exists(path_to_file):
        return os.path.exists(path_to_file)


class LocalFileTransporter(AbstractFileTransporter):
    """Uses a directory to mimic an cloud storage bucket"""

    def __init__(self, bucket_path):
        self.bucket_object = bucket_path
        self.key_storage_path = os.path.join(bucket_path, 'key_storage.json')
        os.makedirs(bucket_path, exist_ok=True)
        with open(self.key_storage_path, 'w+') as fp:
            json.dump({}, fp)

    def upload_file_to_bucket(self, path_to_file, key):
        with open(self.key_storage_path, 'r') as key_storage_fp:
            key_storage = json.load(key_storage_fp)
        key_storage[key] = path_to_file
        with open(self.key_storage_path, 'w') as key_storage_fp:
            json.dump(key_storage, key_storage_fp)


class GoogleCloudStorageFileTransporter(AbstractFileTransporter):
    """Uses google cloud storage sdk to upload/download objects"""

    def __init__(self, bucket_name):
        # TODO: Eventually support custom authentication so we aren't forcing people to setup their environments
        self.client = storage.Client()
        self.bucket_name = bucket_name
        try:
            self.bucket_obj = self.client.get_bucket(self.bucket_name)
        except NotFound as e:
            raise DagsterCloudResourceSDKException(e)

    def upload_file_to_bucket(self, path_to_file, key):
        blob = self.bucket_obj.blob(key)
        try:
            with open(path_to_file, 'r') as fp_to_upload:
                blob.upload_from_file(fp_to_upload)
        except Exception as e:
            raise DagsterCloudResourceSDKException(e)


@resource(config={'bucket_path': Field(String)})
def local_transporter(context):
    return LocalFileTransporter(context.resource_config['bucket_path'])


@resource(config={'bucket_name': Field(String)})
def production_transporter(context):
    return GoogleCloudStorageFileTransporter(context.resource_config['bucket_name'])


@resource
def temporary_directory_mount(_):
    with seven.TemporaryDirectory() as tmpdir_path:
        yield tmpdir_path


@resource(config={'mount_location': Field(String)})
def mount(context):
    mount_location = context.resource_config['mount_location']
    if os.path.exists(mount_location):
        return context.resource_config['mount_location']
    raise NotADirectoryError("Cant mount files on this resource. Make sure it exists!")
