import io
import pickle
from typing import Sequence, Union

from dagster import (
    Field,
    InputContext,
    MemoizableIOManager,
    MetadataValue,
    OutputContext,
    StringSource,
    _check as check,
    io_manager,
)
from dagster._utils import PICKLE_PROTOCOL


class PickledObjectS3IOManager(MemoizableIOManager):
    def __init__(
        self,
        s3_bucket,
        s3_session,
        s3_prefix=None,
    ):
        self.bucket = check.str_param(s3_bucket, "s3_bucket")
        self.s3_prefix = check.opt_str_param(s3_prefix, "s3_prefix")
        self.s3 = s3_session
        self.s3.list_objects(Bucket=self.bucket, Prefix=self.s3_prefix, MaxKeys=1)

    def _get_path(self, context: Union[InputContext, OutputContext]) -> str:
        path: Sequence[str]
        if context.has_asset_key:
            path = context.get_asset_identifier()
        else:
            path = ["storage", *context.get_identifier()]

        return "/".join([self.s3_prefix, *path])

    def has_output(self, context):
        key = self._get_path(context)
        return self._has_object(key)

    def _rm_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")

        # delete_object wont fail even if the item has been deleted.
        self.s3.delete_object(Bucket=self.bucket, Key=key)

    def _has_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")

        found_object = False

        try:
            self.s3.get_object(Bucket=self.bucket, Key=key)
            found_object = True
        except self.s3.exceptions.NoSuchKey:
            found_object = False

        return found_object

    def _uri_for_key(self, key):
        check.str_param(key, "key")
        return "s3://" + self.bucket + "/" + "{key}".format(key=key)

    def load_input(self, context):
        if context.dagster_type.typing_type == type(None):
            return None

        key = self._get_path(context)
        context.log.debug(f"Loading S3 object from: {self._uri_for_key(key)}")
        obj = pickle.loads(self.s3.get_object(Bucket=self.bucket, Key=key)["Body"].read())

        return obj

    def handle_output(self, context, obj):
        if context.dagster_type.typing_type == type(None):
            check.invariant(
                obj is None,
                (
                    "Output had Nothing type or 'None' annotation, but handle_output received"
                    f" value that was not None and was of type {type(obj)}."
                ),
            )
            return None

        key = self._get_path(context)
        path = self._uri_for_key(key)
        context.log.debug(f"Writing S3 object at: {path}")

        if self._has_object(key):
            context.log.warning(f"Removing existing S3 key: {key}")
            self._rm_object(key)

        pickled_obj = pickle.dumps(obj, PICKLE_PROTOCOL)
        pickled_obj_bytes = io.BytesIO(pickled_obj)
        self.s3.upload_fileobj(pickled_obj_bytes, self.bucket, key)
        context.add_output_metadata({"uri": MetadataValue.path(path)})


@io_manager(
    config_schema={
        "s3_bucket": Field(StringSource),
        "s3_prefix": Field(StringSource, is_required=False, default_value="dagster"),
    },
    required_resource_keys={"s3"},
)
def s3_pickle_io_manager(init_context):
    """Persistent IO manager using S3 for storage.

    Serializes objects via pickling. Suitable for objects storage for distributed executors, so long
    as each execution node has network connectivity and credentials for S3 and the backing bucket.

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

        from dagster import asset, repository, with_resources
        from dagster_aws.s3 import s3_pickle_io_manager, s3_resource


        @asset
        def asset1():
            # create df ...
            return df

        @asset
        def asset2(asset1):
            return df[:5]

        @repository
        def repo():
            return with_resources(
                [asset1, asset2],
                resource_defs={
                    "io_manager": s3_pickle_io_manager.configured(
                        {"s3_bucket": "my-cool-bucket", "s3_prefix": "my-cool-prefix"}
                    ),
                    "s3": s3_resource,
                },
            )
        )


    2. Attach this IO manager to your job to make it available to your ops.

    .. code-block:: python

        from dagster import job
        from dagster_aws.s3 import s3_pickle_io_manager, s3_resource

        @job(
            resource_defs={
                "io_manager": s3_pickle_io_manager.configured(
                    {"s3_bucket": "my-cool-bucket", "s3_prefix": "my-cool-prefix"}
                ),
                "s3": s3_resource,
            },
        )
        def my_job():
            ...
    """
    s3_session = init_context.resources.s3
    s3_bucket = init_context.resource_config["s3_bucket"]
    s3_prefix = init_context.resource_config.get("s3_prefix")  # s3_prefix is optional
    pickled_io_manager = PickledObjectS3IOManager(s3_bucket, s3_session, s3_prefix=s3_prefix)
    return pickled_io_manager
