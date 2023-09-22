import pickle
from typing import Any, Optional, Union

from dagster import (
    ConfigurableIOManager,
    InputContext,
    OutputContext,
    ResourceDependency,
    _check as check,
    io_manager,
)
from dagster._annotations import deprecated
from dagster._core.storage.io_manager import dagster_maintained_io_manager
from dagster._core.storage.upath_io_manager import UPathIOManager
from dagster._utils import PICKLE_PROTOCOL
from dagster._utils.backoff import backoff
from dagster._utils.cached_method import cached_method
from google.api_core.exceptions import Forbidden, ServiceUnavailable, TooManyRequests
from google.cloud import storage
from pydantic import Field
from upath import UPath

from .resources import GCSResource

DEFAULT_LEASE_DURATION = 60  # One minute


class PickledObjectGCSIOManager(UPathIOManager):
    def __init__(self, bucket: str, client: Optional[Any] = None, prefix: str = "dagster"):
        self.bucket = check.str_param(bucket, "bucket")
        self.client = client or storage.Client()
        self.bucket_obj = self.client.bucket(bucket)
        check.invariant(self.bucket_obj.exists())
        self.prefix = check.str_param(prefix, "prefix")
        super().__init__(base_path=UPath(self.prefix))

    def unlink(self, path: UPath) -> None:
        key = str(path)
        if self.bucket_obj.blob(key).exists():
            self.bucket_obj.blob(key).delete()

    def path_exists(self, path: UPath) -> bool:
        key = str(path)
        blobs = self.client.list_blobs(self.bucket, prefix=key)
        return len(list(blobs)) > 0

    def get_op_output_relative_path(self, context: Union[InputContext, OutputContext]) -> UPath:
        parts = context.get_identifier()
        run_id = parts[0]
        output_parts = parts[1:]
        return UPath("storage", run_id, "files", *output_parts)

    def get_loading_input_log_message(self, path: UPath) -> str:
        return f"Loading GCS object from: {self._uri_for_path(path)}"

    def get_writing_output_log_message(self, path: UPath) -> str:
        return f"Writing GCS object at: {self._uri_for_path(path)}"

    def _uri_for_path(self, path: UPath) -> str:
        return f"gs://{self.bucket}/{path}"

    def make_directory(self, path: UPath) -> None:
        # It is not necessary to create directories in GCP
        return None

    def load_from_path(self, context: InputContext, path: UPath) -> Any:
        bytes_obj = self.bucket_obj.blob(str(path)).download_as_bytes()
        return pickle.loads(bytes_obj)

    def dump_to_path(self, context: OutputContext, obj: Any, path: UPath) -> None:
        if self.path_exists(path):
            context.log.warning(f"Removing existing GCS key: {path}")
            self.unlink(path)

        pickled_obj = pickle.dumps(obj, PICKLE_PROTOCOL)

        backoff(
            self.bucket_obj.blob(str(path)).upload_from_string,
            args=[pickled_obj],
            retry_on=(TooManyRequests, Forbidden, ServiceUnavailable),
        )


class GCSPickleIOManager(ConfigurableIOManager):
    """Persistent IO manager using GCS for storage.

    Serializes objects via pickling. Suitable for objects storage for distributed executors, so long
    as each execution node has network connectivity and credentials for GCS and the backing bucket.

    Assigns each op output to a unique filepath containing run ID, step key, and output name.
    Assigns each asset to a single filesystem path, at ``<base_dir>/<asset_key>``. If the asset key
    has multiple components, the final component is used as the name of the file, and the preceding
    components as parent directories under the base_dir.

    Subsequent materializations of an asset will overwrite previous materializations of that asset.
    With a base directory of ``/my/base/path``, an asset with key
    ``AssetKey(["one", "two", "three"])`` would be stored in a file called ``three`` in a directory
    with path ``/my/base/path/one/two/``.

    Example usage:

    1. Attach this IO manager to a set of assets.

    .. code-block:: python

        from dagster import asset, Definitions
        from dagster_gcp.gcs import GCSPickleIOManager, GCSResource

        @asset
        def asset1():
            # create df ...
            return df

        @asset
        def asset2(asset1):
            return asset1[:5]

        defs = Definitions(
            assets=[asset1, asset2],
            resources={
                "io_manager": GCSPickleIOManager(
                    gcs_bucket="my-cool-bucket",
                    gcs_prefix="my-cool-prefix"
                ),
                "gcs": GCSResource(project="my-cool-project")
            }
        )


    2. Attach this IO manager to your job to make it available to your ops.

    .. code-block:: python

        from dagster import job
        from dagster_gcp.gcs import GCSPickleIOManager, GCSResource

        @job(
            resource_defs={
                "io_manager": GCSPickleIOManager(
                    gcs=GCSResource(project="my-cool-project")
                    gcs_bucket="my-cool-bucket",
                    gcs_prefix="my-cool-prefix"
                ),
            }
        )
        def my_job():
            ...
    """

    gcs: ResourceDependency[GCSResource]
    gcs_bucket: str = Field(description="GCS bucket to store files")
    gcs_prefix: str = Field(default="dagster", description="Prefix to add to all file paths")

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    @property
    @cached_method
    def _internal_io_manager(self) -> PickledObjectGCSIOManager:
        return PickledObjectGCSIOManager(
            bucket=self.gcs_bucket, client=self.gcs.get_client(), prefix=self.gcs_prefix
        )

    def load_input(self, context: InputContext) -> Any:
        return self._internal_io_manager.load_input(context)

    def handle_output(self, context: OutputContext, obj: Any) -> None:
        self._internal_io_manager.handle_output(context, obj)


@deprecated(
    breaking_version="2.0",
    additional_warn_text="Please use GCSPickleIOManager instead.",
)
class ConfigurablePickledObjectGCSIOManager(GCSPickleIOManager):
    """Renamed to GCSPickleIOManager. See GCSPickleIOManager for documentation."""

    pass


@dagster_maintained_io_manager
@io_manager(
    config_schema=GCSPickleIOManager.to_config_schema(),
    required_resource_keys={"gcs"},
)
def gcs_pickle_io_manager(init_context):
    """Persistent IO manager using GCS for storage.

    Serializes objects via pickling. Suitable for objects storage for distributed executors, so long
    as each execution node has network connectivity and credentials for GCS and the backing bucket.

    Assigns each op output to a unique filepath containing run ID, step key, and output name.
    Assigns each asset to a single filesystem path, at ``<base_dir>/<asset_key>``. If the asset key
    has multiple components, the final component is used as the name of the file, and the preceding
    components as parent directories under the base_dir.

    Subsequent materializations of an asset will overwrite previous materializations of that asset.
    With a base directory of ``/my/base/path``, an asset with key
    ``AssetKey(["one", "two", "three"])`` would be stored in a file called ``three`` in a directory
    with path ``/my/base/path/one/two/``.

    Example usage:

    1. Attach this IO manager to a set of assets.

    .. code-block:: python

        from dagster import Definitions, asset
        from dagster_gcp.gcs import gcs_pickle_io_manager, gcs_resource

        @asset
        def asset1():
            # create df ...
            return df

        @asset
        def asset2(asset1):
            return asset1[:5]

        defs = Definitions(
            assets=[asset1, asset2],
            resources={
                    "io_manager": gcs_pickle_io_manager.configured(
                        {"gcs_bucket": "my-cool-bucket", "gcs_prefix": "my-cool-prefix"}
                    ),
                    "gcs": gcs_resource.configured({"project": "my-cool-project"}),
                },
        )


    2. Attach this IO manager to your job to make it available to your ops.

    .. code-block:: python

        from dagster import job
        from dagster_gcp.gcs import gcs_pickle_io_manager, gcs_resource

        @job(
            resource_defs={
                "io_manager": gcs_pickle_io_manager.configured(
                    {"gcs_bucket": "my-cool-bucket", "gcs_prefix": "my-cool-prefix"}
                ),
                "gcs": gcs_resource.configured({"project": "my-cool-project"}),
            },
        )
        def my_job():
            ...
    """
    client = init_context.resources.gcs
    pickled_io_manager = PickledObjectGCSIOManager(
        bucket=init_context.resource_config["gcs_bucket"],
        client=client,
        prefix=init_context.resource_config["gcs_prefix"],
    )
    return pickled_io_manager
