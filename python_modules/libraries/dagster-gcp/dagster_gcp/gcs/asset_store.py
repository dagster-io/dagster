import logging
import pickle

from dagster import AssetStore, Field, StringSource, check, resource
from dagster.utils import PICKLE_PROTOCOL
from dagster.utils.backoff import backoff
from google.api_core.exceptions import TooManyRequests
from google.cloud import storage

DEFAULT_LEASE_DURATION = 60  # One minute


class PickledObjectGCSAssetStore(AssetStore):
    def __init__(self, bucket, client=None, prefix="dagster"):
        self.bucket = check.str_param(bucket, "bucket")
        self.client = client or storage.Client()
        self.bucket_obj = self.client.get_bucket(bucket)
        check.invariant(self.bucket_obj.exists())
        self.prefix = check.str_param(prefix, "prefix")

    def _get_path(self, context):
        return "/".join(
            [
                self.prefix,
                "storage",
                context.source_run_id,
                "files",
                context.step_key,
                context.output_name,
            ]
        )

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

    def get_asset(self, context):
        key = self._get_path(context)
        bytes_obj = self.bucket_obj.blob(key).download_as_bytes()
        obj = pickle.loads(bytes_obj)

        return obj

    def set_asset(self, context, obj):
        key = self._get_path(context)
        logging.info("Writing GCS object at: " + self._uri_for_key(key))

        if self._has_object(key):
            logging.warning("Removing existing GCS key: {key}".format(key=key))
            self._rm_object(key)

        pickled_obj = pickle.dumps(obj, PICKLE_PROTOCOL)

        backoff(
            self.bucket_obj.blob(key).upload_from_string,
            args=[pickled_obj],
            retry_on=(TooManyRequests,),
        )


@resource(
    config_schema={
        "gcs_bucket": Field(StringSource),
        "gcs_prefix": Field(StringSource, is_required=False, default_value="dagster"),
    },
)
def gcs_asset_store(init_context):
    """Persistent asset store using GCS for storage.

    Suitable for assets storage for distributed executors, so long as
    each execution node has network connectivity and credentials for GCS and
    the backing bucket.

    Attach this resource definition to a :py:class:`~dagster.ModeDefinition`
    in order to make it available to your pipeline:

    .. code-block:: python

        pipeline_def = PipelineDefinition(
            mode_defs=[
                ModeDefinition(
                    resource_defs={'asset_store': gcs_asset_store, ...},
                ), ...
            ], ...
        )

    You may configure this storage as follows:

    .. code-block:: YAML

        resources:
            asset_store:
                config:
                    gcs_bucket: my-cool-bucket
                    gcs_prefix: good/prefix-for-files-
    """
    # TODO: Add gcs client resource once resource dependencies are enabled.
    client = storage.Client()
    asset_store = PickledObjectGCSAssetStore(
        init_context.resource_config["gcs_bucket"],
        client,
        init_context.resource_config["gcs_prefix"],
    )
    return asset_store
