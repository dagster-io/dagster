import pickle
from typing import Union

from google.api_core.exceptions import Forbidden, TooManyRequests
from google.cloud import storage  # type: ignore

from dagster import Field, IOManager, InputContext, OutputContext, StringSource
from dagster import _check as check
from dagster import io_manager
from dagster._utils import PICKLE_PROTOCOL
from dagster._utils.backoff import backoff

DEFAULT_LEASE_DURATION = 60  # One minute


class PickledObjectGCSIOManager(IOManager):
    def __init__(self, bucket, client=None, prefix="dagster"):
        self.bucket = check.str_param(bucket, "bucket")
        self.client = client or storage.Client()
        self.bucket_obj = self.client.bucket(bucket)
        check.invariant(self.bucket_obj.exists())
        self.prefix = check.str_param(prefix, "prefix")

    def _get_path(self, context: Union[InputContext, OutputContext]) -> str:
        if context.has_asset_key:
            path = context.get_asset_identifier()
        else:
            parts = context.get_identifier()
            run_id = parts[0]
            output_parts = parts[1:]

            path = ["storage", run_id, "files", *output_parts]

        return "/".join([self.prefix, *path])

    def _rm_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")

        if self.bucket_obj.blob(key).exists():
            self.bucket_obj.blob(key).delete()

    def _has_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")
        blobs = self.client.list_blobs(self.bucket, prefix=key)
        return len(list(blobs)) > 0

    def _uri_for_key(self, key):
        check.str_param(key, "key")
        return "gs://" + self.bucket + "/" + "{key}".format(key=key)

    def load_input(self, context):
        if context.dagster_type.typing_type == type(None):
            return None

        key = self._get_path(context)
        context.log.debug(f"Loading GCS object from: {self._uri_for_key(key)}")

        bytes_obj = self.bucket_obj.blob(key).download_as_bytes()
        obj = pickle.loads(bytes_obj)

        return obj

    def handle_output(self, context, obj):
        if context.dagster_type.typing_type == type(None):
            check.invariant(
                obj is None,
                "Output had Nothing type or 'None' annotation, but handle_output received value "
                f"that was not None and was of type {type(obj)}.",
            )
            return None

        key = self._get_path(context)
        context.log.debug(f"Writing GCS object at: {self._uri_for_key(key)}")

        if self._has_object(key):
            context.log.warning(f"Removing existing GCS key: {key}")
            self._rm_object(key)

        pickled_obj = pickle.dumps(obj, PICKLE_PROTOCOL)

        backoff(
            self.bucket_obj.blob(key).upload_from_string,
            args=[pickled_obj],
            retry_on=(TooManyRequests, Forbidden),
        )


@io_manager(
    config_schema={
        "gcs_bucket": Field(StringSource),
        "gcs_prefix": Field(StringSource, is_required=False, default_value="dagster"),
    },
    required_resource_keys={"gcs"},
)
def gcs_pickle_io_manager(init_context):
    """Persistent IO manager using GCS for storage.

    Serializes objects via pickling. Suitable for objects storage for distributed executors, so long
    as each execution node has network connectivity and credentials for GCS and the backing bucket.

    Assigns each op output to a unique filepath containing run ID, step key, and output name.
    Assigns each asset to a single filesystem path, at "<base_dir>/<asset_key>". If the asset key
    has multiple components, the final component is used as the name of the file, and the preceding
    components as parent directories under the base_dir.

    Subsequent materializations of an asset will overwrite previous materializations of that asset.
    With a base directory of "/my/base/path", an asset with key
    `AssetKey(["one", "two", "three"])` would be stored in a file called "three" in a directory
    with path "/my/base/path/one/two/".

    Attach this resource definition to your job to make it available to your ops.

    .. code-block:: python

        @job(resource_defs={'io_manager': gcs_pickle_io_manager, 'gcs': gcs_resource, ...})
        def my_job():
            my_op()

    You may configure this storage as follows:

    .. code-block:: YAML

        resources:
            io_manager:
                config:
                    gcs_bucket: my-cool-bucket
                    gcs_prefix: good/prefix-for-files-
    """
    client = init_context.resources.gcs
    pickled_io_manager = PickledObjectGCSIOManager(
        init_context.resource_config["gcs_bucket"],
        client,
        init_context.resource_config["gcs_prefix"],
    )
    return pickled_io_manager
