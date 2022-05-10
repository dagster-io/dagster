import io
import pickle

from dagster import Field, MemoizableIOManager, StringSource
from dagster import _check as check
from dagster import io_manager
from dagster.utils import PICKLE_PROTOCOL


class PickledObjectS3IOManager(MemoizableIOManager):
    def __init__(
        self,
        s3_bucket,
        s3_session,
        s3_prefix=None,
    ):
        self.bucket = check.str_param(s3_bucket, "s3_bucket")
        self.s3_prefix = check.str_param(s3_prefix, "s3_prefix")
        self.s3 = s3_session
        self.s3.list_objects(Bucket=self.bucket, Prefix=self.s3_prefix, MaxKeys=1)

    def _get_path(self, context):
        return "/".join([self.s3_prefix, "storage", *context.get_output_identifier()])

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
        key = self._get_path(context.upstream_output)
        context.log.debug(f"Loading S3 object from: {self._uri_for_key(key)}")
        obj = pickle.loads(self.s3.get_object(Bucket=self.bucket, Key=key)["Body"].read())

        return obj

    def handle_output(self, context, obj):
        key = self._get_path(context)
        context.log.debug(f"Writing S3 object at: {self._uri_for_key(key)}")

        if self._has_object(key):
            context.log.warning(f"Removing existing S3 key: {key}")
            self._rm_object(key)

        pickled_obj = pickle.dumps(obj, PICKLE_PROTOCOL)
        pickled_obj_bytes = io.BytesIO(pickled_obj)
        self.s3.upload_fileobj(pickled_obj_bytes, self.bucket, key)


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

    Attach this resource definition to your job to make it available to your ops.

    .. code-block:: python

        @job(resource_defs={'io_manager': s3_pickle_io_manager, "s3": s3_resource, ...})
        def my_job():
            ...

    You may configure this storage as follows:

    .. code-block:: YAML

        resources:
            io_manager:
                config:
                    s3_bucket: my-cool-bucket
                    s3_prefix: good/prefix-for-files-
    """
    s3_session = init_context.resources.s3
    s3_bucket = init_context.resource_config["s3_bucket"]
    s3_prefix = init_context.resource_config.get("s3_prefix")  # s3_prefix is optional
    pickled_io_manager = PickledObjectS3IOManager(s3_bucket, s3_session, s3_prefix=s3_prefix)
    return pickled_io_manager


class PickledObjectS3AssetIOManager(PickledObjectS3IOManager):
    def _get_path(self, context):
        return "/".join([self.s3_prefix, *context.get_asset_output_identifier()])


@io_manager(
    config_schema={
        "s3_bucket": Field(StringSource),
        "s3_prefix": Field(StringSource, is_required=False, default_value="dagster"),
    },
    required_resource_keys={"s3"},
)
def s3_pickle_asset_io_manager(init_context):
    """Persistent IO manager using S3 for storage, meant for use with software-defined assets.

    Each asset is assigned to a single filesystem path, so subsequent materializations of an asset
    will overwrite previous materializations of that asset.

    Serializes objects via pickling. Suitable for objects storage for distributed executors, so long
    as each execution node has network connectivity and credentials for S3 and the backing bucket.

    Attach this resource definition to your job to make it available to your ops.

    .. code-block:: python

        asset_group = AssetGroup(
            assets...,
            resource_defs={'io_manager': s3_pickle_asset_io_manager, "s3": s3_resource, ...}),
        )

    You may configure this IO manager as follows:

    .. code-block:: YAML

        resources:
            io_manager:
                config:
                    s3_bucket: my-cool-bucket
                    s3_prefix: good/prefix-for-files-
    """
    s3_session = init_context.resources.s3
    s3_bucket = init_context.resource_config["s3_bucket"]
    s3_prefix = init_context.resource_config.get("s3_prefix")  # s3_prefix is optional
    pickled_io_manager = PickledObjectS3AssetIOManager(s3_bucket, s3_session, s3_prefix=s3_prefix)
    return pickled_io_manager
