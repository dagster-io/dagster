import json
import os
import shutil
from abc import ABCMeta, abstractmethod

from google.cloud import storage
from six import with_metaclass

from dagster import Field, List, String, resource, seven


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

    def download_file_from_bucket(self, key, path_to_file):
        with open(self.key_storage_path, 'r') as key_storage_fp:
            key_storage = json.load(key_storage_fp)
        if key not in key_storage:
            raise ValueError("Key {} not found in bucket {}".format(key, self.bucket_object))

        shutil.copyfile(key_storage[key], path_to_file)
        return path_to_file


class GoogleCloudStorageFileTransporter(AbstractFileTransporter):
    """Uses google cloud storage sdk to upload/download objects"""

    def __init__(self, bucket_name):
        # TODO: Eventually support custom authentication so we aren't forcing people to setup their environments
        self.client = storage.Client()
        self.bucket_name = bucket_name
        self.bucket_obj = self.client.get_bucket(self.bucket_name)

    def upload_file_to_bucket(self, path_to_file, key):
        blob = self.bucket_obj.blob(key)
        with open(path_to_file, 'r') as fp_to_upload:
            blob.upload_from_file(fp_to_upload)

    def download_file_from_bucket(self, key, path_to_file):
        blob = self.bucket_obj.blob(key)
        with open(path_to_file, 'wb+') as path_to_file:
            blob.download_to_file(path_to_file)
        return path_to_file


class CredentialsVault:
    def __init__(self, credentials):
        self.credentials = credentials

    @classmethod
    def instantiate_vault_from_environment_variables(cls, environment_variable_names):
        '''Will clobber creds that are already in the vault'''
        credentials = {}
        for environment_variable_name in environment_variable_names:
            credential = os.environ.get(environment_variable_name)
            if not credential:
                raise ValueError(
                    "Global Variable {} Not Set in Environment".format(environment_variable_name)
                )
            credentials[environment_variable_name] = credential
        return cls(credentials)


@resource(config={'environment_variable_names': Field(List[str])})
def credentials_vault(context):
    return CredentialsVault.instantiate_vault_from_environment_variables(
        context.resource_config['environment_variable_names']
    )


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
