import pickle
from contextlib import contextmanager

from dagster_azure.adls2.utils import ResourceNotFoundError

from dagster import Field, IOManager, StringSource
from dagster import _check as check
from dagster import io_manager
from dagster.utils import PICKLE_PROTOCOL

_LEASE_DURATION = 60  # One minute


class PickledObjectADLS2IOManager(IOManager):
    def __init__(
        self, file_system, adls2_client, blob_client, lease_client_constructor, prefix="dagster"
    ):
        self.adls2_client = adls2_client
        self.file_system_client = self.adls2_client.get_file_system_client(file_system)
        # We also need a blob client to handle copying as ADLS doesn't have a copy API yet
        self.blob_client = blob_client
        self.blob_container_client = self.blob_client.get_container_client(file_system)
        self.prefix = check.str_param(prefix, "prefix")

        self.lease_client_constructor = lease_client_constructor
        self.lease_duration = _LEASE_DURATION
        self.file_system_client.get_file_system_properties()

    def _get_path(self, context):
        keys = context.get_output_identifier()
        run_id = keys[0]
        output_identifiers = keys[1:]  # variable length because of mapping key
        return "/".join(
            [
                self.prefix,
                "storage",
                run_id,
                "files",
                *output_identifiers,
            ]
        )

    def _rm_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")

        file_client = self.file_system_client.get_file_client(key)
        with self._acquire_lease(file_client, is_rm=True) as lease:
            file_client.delete_file(lease=lease, recursive=True)

    def _has_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")

        try:
            file = self.file_system_client.get_file_client(key)
            file.get_file_properties()
            return True
        except ResourceNotFoundError:
            return False

    def _uri_for_key(self, key, protocol=None):
        check.str_param(key, "key")
        protocol = check.opt_str_param(protocol, "protocol", default="abfss://")
        return "{protocol}{filesystem}@{account}.dfs.core.windows.net/{key}".format(
            protocol=protocol,
            filesystem=self.file_system_client.file_system_name,
            account=self.file_system_client.account_name,
            key=key,
        )

    @contextmanager
    def _acquire_lease(self, client, is_rm=False):
        lease_client = self.lease_client_constructor(client=client)
        try:
            lease_client.acquire(lease_duration=self.lease_duration)
            yield lease_client.id
        finally:
            # cannot release a lease on a file that no longer exists, so need to check
            if not is_rm:
                lease_client.release()

    def load_input(self, context):
        key = self._get_path(context.upstream_output)
        context.log.debug(f"Loading ADLS2 object from: {self._uri_for_key(key)}")
        file = self.file_system_client.get_file_client(key)
        stream = file.download_file()
        obj = pickle.loads(stream.readall())

        return obj

    def handle_output(self, context, obj):
        key = self._get_path(context)
        context.log.debug(f"Writing ADLS2 object at: {self._uri_for_key(key)}")

        if self._has_object(key):
            context.log.warning(f"Removing existing ADLS2 key: {key}")
            self._rm_object(key)

        pickled_obj = pickle.dumps(obj, PICKLE_PROTOCOL)

        file = self.file_system_client.create_file(key)
        with self._acquire_lease(file) as lease:
            file.upload_data(pickled_obj, lease=lease, overwrite=True)


@io_manager(
    config_schema={
        "adls2_file_system": Field(StringSource, description="ADLS Gen2 file system name"),
        "adls2_prefix": Field(StringSource, is_required=False, default_value="dagster"),
    },
    required_resource_keys={"adls2"},
)
def adls2_pickle_io_manager(init_context):
    """Persistent IO manager using Azure Data Lake Storage Gen2 for storage.

    Serializes objects via pickling. Suitable for objects storage for distributed executors, so long
    as each execution node has network connectivity and credentials for ADLS and the backing
    container.

    Attach this resource definition to your job in order to make it available all your ops:

    .. code-block:: python

        @job(resource_defs={
            'io_manager': adls2_pickle_io_manager,
            'adls2': adls2_resource,
            ...,
        })
        def my_job():
            ...

    You may configure this storage as follows:

    .. code-block:: YAML

        resources:
            io_manager:
                config:
                    adls2_file_system: my-cool-file-system
                    adls2_prefix: good/prefix-for-files-
    """
    adls_resource = init_context.resources.adls2
    adls2_client = adls_resource.adls2_client
    blob_client = adls_resource.blob_client
    lease_client = adls_resource.lease_client_constructor
    pickled_io_manager = PickledObjectADLS2IOManager(
        init_context.resource_config["adls2_file_system"],
        adls2_client,
        blob_client,
        lease_client,
        init_context.resource_config.get("adls2_prefix"),
    )
    return pickled_io_manager


class PickledObjectADLS2AssetIOManager(PickledObjectADLS2IOManager):
    def _get_path(self, context):
        return "/".join([self.prefix, *context.get_asset_output_identifier()])


@io_manager(
    config_schema={
        "adls2_file_system": Field(StringSource, description="ADLS Gen2 file system name"),
        "adls2_prefix": Field(StringSource, is_required=False, default_value="dagster"),
    },
    required_resource_keys={"adls2"},
)
def adls2_pickle_asset_io_manager(init_context):
    """Persistent IO manager using Azure Data Lake Storage Gen2 for storage, meant for use with
    software-defined assets.

    Each asset is assigned to a single filesystem path, so subsequent materializations of an asset
    will overwrite previous materializations of that asset.

    Serializes objects via pickling. Suitable for objects storage for distributed executors, so long
    as each execution node has network connectivity and credentials for ADLS and the backing
    container.

    Attach this resource definition to your job in order to make it available all your ops:

    .. code-block:: python

        asset_group = AssetGroup(
            assets...,
            resource_defs={'io_manager': adls2_pickle_io_manager, "adls2": adls2_resource, ...}),
        )

    You may configure this storage as follows:

    .. code-block:: YAML

        resources:
            io_manager:
                config:
                    adls2_file_system: my-cool-file-system
                    adls2_prefix: good/prefix-for-files
    """
    adls_resource = init_context.resources.adls2
    adls2_client = adls_resource.adls2_client
    blob_client = adls_resource.blob_client
    lease_client = adls_resource.lease_client_constructor
    pickled_io_manager = PickledObjectADLS2AssetIOManager(
        init_context.resource_config["adls2_file_system"],
        adls2_client,
        blob_client,
        lease_client,
        init_context.resource_config.get("adls2_prefix"),
    )
    return pickled_io_manager
