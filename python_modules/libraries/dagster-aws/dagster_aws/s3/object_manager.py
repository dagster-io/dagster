import logging
import pickle

from dagster import Field, ObjectManager, StringSource, check, object_manager
from dagster.utils import PICKLE_PROTOCOL


class PickledObjectS3ObjectManager(ObjectManager):
    def __init__(
        self, s3_bucket, s3_session, s3_prefix=None,
    ):
        self.bucket = check.str_param(s3_bucket, "s3_bucket")
        self.s3_prefix = check.str_param(s3_prefix, "s3_prefix")
        self.s3 = s3_session
        self.s3.head_bucket(Bucket=self.bucket)

    def _get_path(self, context):
        return "/".join([self.s3_prefix, "storage", *context.get_run_scoped_output_identifier()])

    def _last_key(self, key):
        if "/" not in key:
            return key
        comps = key.split("/")
        return comps[-1]

    def _rm_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")

        def delete_for_results(store, results):
            store.s3.delete_objects(
                Bucket=store.bucket,
                Delete={"Objects": [{"Key": result["Key"]} for result in results["Contents"]]},
            )

        if self._has_object(key):
            results = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=key)
            delete_for_results(self, results)

            continuation = results["IsTruncated"]
            while continuation:
                continuation_token = results["NextContinuationToken"]
                results = self.s3.list_objects_v2(
                    Bucket=self.bucket, Prefix=key, ContinuationToken=continuation_token
                )
                delete_for_results(self, results)
                continuation = results["IsTruncated"]

    def _has_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")

        key_count = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=key)["KeyCount"]
        return bool(key_count > 0)

    def _uri_for_key(self, key):
        check.str_param(key, "key")
        return "s3://" + self.bucket + "/" + "{key}".format(key=key)

    def load_input(self, context):
        key = self._get_path(context.upstream_output)
        obj = pickle.loads(self.s3.get_object(Bucket=self.bucket, Key=key)["Body"].read())

        return obj

    def handle_output(self, context, obj):
        key = self._get_path(context)
        logging.info("Writing S3 object at: " + self._uri_for_key(key))

        if self._has_object(key):
            logging.warning("Removing existing S3 key: {key}".format(key=key))
            self._rm_object(key)

        pickled_obj = pickle.dumps(obj, PICKLE_PROTOCOL)
        self.s3.put_object(Bucket=self.bucket, Key=key, Body=pickled_obj)


@object_manager(
    config_schema={
        "s3_bucket": Field(StringSource),
        "s3_prefix": Field(StringSource, is_required=False, default_value="dagster"),
    },
    required_resource_keys={"s3"},
)
def s3_object_manager(init_context):
    """Persistent object manager using S3 for storage.

    Suitable for objects storage for distributed executors, so long as
    each execution node has network connectivity and credentials for S3 and
    the backing bucket.

    Attach this resource definition to a :py:class:`~dagster.ModeDefinition`
    in order to make it available to your pipeline:

    .. code-block:: python

        pipeline_def = PipelineDefinition(
            mode_defs=[
                ModeDefinition(
                    resource_defs={'object_manager': s3_object_manager, "s3": s3_resource, ...},
                ), ...
            ], ...
        )

    You may configure this storage as follows:

    .. code-block:: YAML

        resources:
            object_manager:
                config:
                    s3_bucket: my-cool-bucket
                    s3_prefix: good/prefix-for-files-
    """
    s3_session = init_context.resources.s3
    s3_bucket = init_context.resource_config["s3_bucket"]
    s3_prefix = init_context.resource_config.get("s3_prefix")  # s3_prefix is optional
    pickled_object_manager = PickledObjectS3ObjectManager(
        s3_bucket, s3_session, s3_prefix=s3_prefix
    )
    return pickled_object_manager
