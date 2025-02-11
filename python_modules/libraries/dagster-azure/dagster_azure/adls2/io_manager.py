import pickle
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Union

from dagster import (
    InputContext,
    OutputContext,
    ResourceDependency,
    _check as check,
    io_manager,
)
from dagster._annotations import deprecated
from dagster._config.pythonic_config import ConfigurableIOManager
from dagster._core.execution.context.init import InitResourceContext
from dagster._core.storage.io_manager import dagster_maintained_io_manager
from dagster._core.storage.upath_io_manager import UPathIOManager
from dagster._utils import PICKLE_PROTOCOL
from dagster._utils.cached_method import cached_method
from pydantic import Field
from upath import UPath

from dagster_azure.adls2.resources import ADLS2Resource
from dagster_azure.adls2.utils import (
    DataLakeLeaseClient,
    DataLakeServiceClient,
    ResourceNotFoundError,
)
from dagster_azure.blob.utils import BlobLeaseClient, BlobServiceClient


class PickledObjectADLS2IOManager(UPathIOManager):
    def __init__(
        self,
        file_system: str,
        adls2_client: DataLakeServiceClient,
        blob_client: BlobServiceClient,
        lease_client_constructor: Union[type[DataLakeLeaseClient], type[BlobLeaseClient]],
        prefix: str = "dagster",
        lease_duration: int = 60,
    ):
        if lease_duration != -1 and (lease_duration < 15 or lease_duration > 60):
            raise ValueError("lease_duration must be -1 (unlimited) or between 15 and 60")

        self.adls2_client = adls2_client
        self.file_system_client = self.adls2_client.get_file_system_client(file_system)
        # We also need a blob client to handle copying as ADLS doesn't have a copy API yet
        self.blob_client = blob_client
        self.blob_container_client = self.blob_client.get_container_client(file_system)
        self.prefix = check.str_param(prefix, "prefix")

        self.lease_client_constructor = lease_client_constructor
        self.lease_duration = lease_duration
        self.file_system_client.get_file_system_properties()
        super().__init__(base_path=UPath(self.prefix))

    def get_op_output_relative_path(self, context: Union[InputContext, OutputContext]) -> UPath:
        parts = context.get_identifier()
        run_id = parts[0]
        output_parts = parts[1:]
        return UPath("storage", run_id, "files", *output_parts)

    def get_loading_input_log_message(self, path: UPath) -> str:
        return f"Loading ADLS2 object from: {self._uri_for_path(path)}"

    def get_writing_output_log_message(self, path: UPath) -> str:
        return f"Writing ADLS2 object at: {self._uri_for_path(path)}"

    def unlink(self, path: UPath) -> None:
        file_client = self.file_system_client.get_file_client(path.as_posix())
        with self._acquire_lease(file_client, is_rm=True) as lease:
            file_client.delete_file(lease=lease, recursive=True)

    def make_directory(self, path: UPath) -> None:
        # It is not necessary to create directories in ADLS2
        return None

    def path_exists(self, path: UPath) -> bool:
        try:
            self.file_system_client.get_file_client(path.as_posix()).get_file_properties()
        except ResourceNotFoundError:
            return False
        return True

    def _uri_for_path(self, path: UPath, protocol: str = "abfss://") -> str:
        return f"{protocol}{self.file_system_client.file_system_name}@{self.file_system_client.account_name}.dfs.core.windows.net/{path.as_posix()}"

    @contextmanager
    def _acquire_lease(self, client: Any, is_rm: bool = False) -> Iterator[str]:
        lease_client = self.lease_client_constructor(client=client)
        try:
            # Unclear why this needs to be type-ignored
            lease_client.acquire(lease_duration=self.lease_duration)  # type: ignore
            yield lease_client.id
        finally:
            # cannot release a lease on a file that no longer exists, so need to check
            if not is_rm:
                lease_client.release()

    def load_from_path(self, context: InputContext, path: UPath) -> Any:
        if context.dagster_type.typing_type == type(None):
            return None
        file = self.file_system_client.get_file_client(path.as_posix())
        stream = file.download_file()
        return pickle.loads(stream.readall())

    def dump_to_path(self, context: OutputContext, obj: Any, path: UPath) -> None:
        if self.path_exists(path):
            context.log.warning(f"Removing existing ADLS2 key: {path}")
            self.unlink(path)

        pickled_obj = pickle.dumps(obj, PICKLE_PROTOCOL)
        file = self.file_system_client.create_file(path.as_posix())
        with self._acquire_lease(file) as lease:
            file.upload_data(pickled_obj, lease=lease, overwrite=True)


class ADLS2PickleIOManager(ConfigurableIOManager):
    """Persistent IO manager using Azure Data Lake Storage Gen2 for storage.

    Serializes objects via pickling. Suitable for objects storage for distributed executors, so long
    as each execution node has network connectivity and credentials for ADLS and the backing
    container.

    Assigns each op output to a unique filepath containing run ID, step key, and output name.
    Assigns each asset to a single filesystem path, at "<base_dir>/<asset_key>". If the asset key
    has multiple components, the final component is used as the name of the file, and the preceding
    components as parent directories under the base_dir.

    Subsequent materializations of an asset will overwrite previous materializations of that asset.
    With a base directory of "/my/base/path", an asset with key
    `AssetKey(["one", "two", "three"])` would be stored in a file called "three" in a directory
    with path "/my/base/path/one/two/".

    Example usage:

    1. Attach this IO manager to a set of assets.

    .. code-block:: python

        from dagster import Definitions, asset
        from dagster_azure.adls2 import ADLS2PickleIOManager, ADLS2Resource, ADLS2SASToken

        @asset
        def asset1():
            # create df ...
            return df

        @asset
        def asset2(asset1):
            return df[:5]

        defs = Definitions(
            assets=[asset1, asset2],
            resources={
                "io_manager": ADLS2PickleIOManager(
                    adls2_file_system="my-cool-fs",
                    adls2_prefix="my-cool-prefix",
                    adls2=ADLS2Resource(
                        storage_account="my-storage-account",
                        credential=ADLS2SASToken(token="my-sas-token"),
                    ),
                ),
            },
        )


    2. Attach this IO manager to your job to make it available to your ops.

    .. code-block:: python

        from dagster import job
        from dagster_azure.adls2 import ADLS2PickleIOManager, ADLS2Resource, ADLS2SASToken

        @job(
            resource_defs={
                "io_manager": ADLS2PickleIOManager(
                    adls2_file_system="my-cool-fs",
                    adls2_prefix="my-cool-prefix",
                    adls2=ADLS2Resource(
                        storage_account="my-storage-account",
                        credential=ADLS2SASToken(token="my-sas-token"),
                    ),
                ),
            },
        )
        def my_job():
            ...
    """

    adls2: ResourceDependency[ADLS2Resource]
    adls2_file_system: str = Field(description="ADLS Gen2 file system name.")
    adls2_prefix: str = Field(
        default="dagster", description="ADLS Gen2 file system prefix to write to."
    )
    lease_duration: int = Field(
        default=60,
        description="Lease duration in seconds. Must be between 15 and 60 seconds or -1 for infinite.",
    )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @property
    @cached_method
    def _internal_io_manager(self) -> PickledObjectADLS2IOManager:
        return PickledObjectADLS2IOManager(
            self.adls2_file_system,
            self.adls2.adls2_client,
            self.adls2.blob_client,
            self.adls2.lease_client_constructor,
            self.adls2_prefix,
            self.lease_duration,
        )

    def load_input(self, context: "InputContext") -> Any:
        return self._internal_io_manager.load_input(context)

    def handle_output(self, context: "OutputContext", obj: Any) -> None:
        self._internal_io_manager.handle_output(context, obj)


@deprecated(
    breaking_version="2.0",
    additional_warn_text="Please use ADLS2PickleIOManager instead.",
)
class ConfigurablePickledObjectADLS2IOManager(ADLS2PickleIOManager):
    """Renamed to ADLS2PickleIOManager. See ADLS2PickleIOManager for documentation."""

    pass


@dagster_maintained_io_manager
@io_manager(
    config_schema=ADLS2PickleIOManager.to_config_schema(),
    required_resource_keys={"adls2"},
)
def adls2_pickle_io_manager(init_context: InitResourceContext) -> PickledObjectADLS2IOManager:
    """Persistent IO manager using Azure Data Lake Storage Gen2 for storage.

    Serializes objects via pickling. Suitable for objects storage for distributed executors, so long
    as each execution node has network connectivity and credentials for ADLS and the backing
    container.

    Assigns each op output to a unique filepath containing run ID, step key, and output name.
    Assigns each asset to a single filesystem path, at "<base_dir>/<asset_key>". If the asset key
    has multiple components, the final component is used as the name of the file, and the preceding
    components as parent directories under the base_dir.

    Subsequent materializations of an asset will overwrite previous materializations of that asset.
    With a base directory of "/my/base/path", an asset with key
    `AssetKey(["one", "two", "three"])` would be stored in a file called "three" in a directory
    with path "/my/base/path/one/two/".

    Example usage:

    Attach this IO manager to a set of assets.

    .. code-block:: python

        from dagster import Definitions, asset
        from dagster_azure.adls2 import adls2_pickle_io_manager, adls2_resource

        @asset
        def asset1():
            # create df ...
            return df

        @asset
        def asset2(asset1):
            return df[:5]

        defs = Definitions(
            assets=[asset1, asset2],
            resources={
                "io_manager": adls2_pickle_io_manager.configured(
                    {"adls2_file_system": "my-cool-fs", "adls2_prefix": "my-cool-prefix"}
                ),
                "adls2": adls2_resource,
            },
        )


    Attach this IO manager to your job to make it available to your ops.

    .. code-block:: python

        from dagster import job
        from dagster_azure.adls2 import adls2_pickle_io_manager, adls2_resource

        @job(
            resource_defs={
                "io_manager": adls2_pickle_io_manager.configured(
                    {"adls2_file_system": "my-cool-fs", "adls2_prefix": "my-cool-prefix"}
                ),
                "adls2": adls2_resource,
            },
        )
        def my_job():
            ...
    """
    adls_resource = init_context.resources.adls2
    adls2_client = adls_resource.adls2_client
    blob_client = adls_resource.blob_client
    lease_client = adls_resource.lease_client_constructor
    return PickledObjectADLS2IOManager(
        init_context.resource_config["adls2_file_system"],
        adls2_client,
        blob_client,
        lease_client,
        init_context.resource_config.get("adls2_prefix"),
        init_context.resource_config.get("lease_duration"),
    )
