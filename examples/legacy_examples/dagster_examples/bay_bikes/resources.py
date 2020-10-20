import os
import shutil
import tempfile

from dagster import check, resource, seven
from dagster.utils import mkdir_p
from google.cloud import storage


class CredentialsVault(object):
    def __init__(self, credentials):
        self.credentials = credentials

    @classmethod
    def instantiate_vault_from_environment_variables(cls, environment_variable_names):
        """Will clobber creds that are already in the vault"""
        credentials = {}
        for environment_variable_name in environment_variable_names:
            credential = os.environ.get(environment_variable_name)
            if not credential:
                raise ValueError(
                    "Global Variable {} Not Set in Environment".format(environment_variable_name)
                )
            credentials[environment_variable_name] = credential
        return cls(credentials)


@resource(config_schema={"environment_variable_names": [str]})
def credentials_vault(context):
    return CredentialsVault.instantiate_vault_from_environment_variables(
        context.resource_config["environment_variable_names"]
    )


@resource
def temporary_directory_mount(_):
    with seven.TemporaryDirectory() as tmpdir_path:
        yield tmpdir_path


@resource(config_schema={"mount_location": str})
def mount(context):
    mount_location = context.resource_config["mount_location"]
    if os.path.exists(mount_location):
        return context.resource_config["mount_location"]
    raise NotADirectoryError("Cant mount files on this resource. Make sure it exists!")


@resource
def gcs_client(_):
    return storage.Client()


class LocalBlob:
    def __init__(self, key, bucket_location):
        self.key = check.str_param(key, "key")
        self.location = os.path.join(check.str_param(bucket_location, "bucket_location"), key)

    def upload_from_file(self, file_buffer):
        if os.path.exists(self.location):
            os.remove(self.location)
        with open(self.location, "w+b") as fdest:
            shutil.copyfileobj(file_buffer, fdest)


class LocalBucket:
    def __init__(self, bucket_name, volume):
        self.bucket_name = check.str_param(bucket_name, "bucket_name")
        # Setup bucket
        self.volume = os.path.join(tempfile.gettempdir(), check.str_param(volume, "volume"))
        bucket_location = os.path.join(self.volume, self.bucket_name)
        if not os.path.exists(bucket_location):
            mkdir_p(bucket_location)
        self.location = bucket_location
        self.blobs = {}

    def blob(self, key):
        check.str_param(key, "key")
        if key not in self.blobs:
            self.blobs[key] = LocalBlob(key, self.location)
        return self.blobs[key]


class LocalClient:
    def __init__(self, volume="storage"):
        self.buckets = {}
        self.volume = check.str_param(volume, "volume")

    def get_bucket(self, bucket_name):
        check.str_param(bucket_name, "bucket_name")
        if bucket_name not in self.buckets:
            self.buckets[bucket_name] = LocalBucket(bucket_name, self.volume)
        return self.buckets[bucket_name]


@resource
def local_client(_):
    return LocalClient()


@resource
def testing_client(_):
    return LocalClient(volume="testing-storage")
