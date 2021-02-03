import pickle

from dagster import Field, IOManager, StringSource, check, io_manager
from dagster.utils import PICKLE_PROTOCOL
from dagster.utils.backoff import backoff
from google.api_core.exceptions import TooManyRequests
from google.cloud import storage

DEFAULT_LEASE_DURATION = 60  # One minute


class PickledObjectGCSIOManager(IOManager):
    def __init__(self, bucket, client=None, prefix="dagster"):
        self.bucket = check.str_param(bucket, "bucket")
        self.client = client or storage.Client()
        self.bucket_obj = self.client.get_bucket(bucket)
        check.invariant(self.bucket_obj.exists())
        self.prefix = check.str_param(prefix, "prefix")

    def _get_path(self, context):
        run_id, step_key, name = context.get_run_scoped_output_identifier()
        return "/".join(
            [
                self.prefix,
                "storage",
                run_id,
                "files",
                step_key,
                name,
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

    def load_input(self, context):
        key = self._get_path(context.upstream_output)
        context.log.debug(f"Loading GCS object from: {self._uri_for_key(key)}")

        bytes_obj = self.bucket_obj.blob(key).download_as_bytes()
        obj = pickle.loads(bytes_obj)

        return obj

    def handle_output(self, context, obj):
        key = self._get_path(context)
        context.log.debug(f"Writing GCS object at: {self._uri_for_key(key)}")

        if self._has_object(key):
            context.log.warning(f"Removing existing GCS key: {key}")
            self._rm_object(key)

        pickled_obj = pickle.dumps(obj, PICKLE_PROTOCOL)

        backoff(
            self.bucket_obj.blob(key).upload_from_string,
            args=[pickled_obj],
            retry_on=(TooManyRequests,),
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

    Attach this resource definition to a :py:class:`~dagster.ModeDefinition`
    in order to make it available to your pipeline:

    .. code-block:: python

        pipeline_def = PipelineDefinition(
            mode_defs=[
                ModeDefinition(
                    resource_defs={'io_manager': gcs_pickle_io_manager, 'gcs': gcs_resource, ...},
                ), ...
            ], ...
        )

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
