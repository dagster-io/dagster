import logging
import sys
from io import BytesIO, StringIO

from dagster import check
from dagster.core.storage.object_store import ObjectStore
from dagster.core.types.marshal import SerializationStrategy
from dagster.utils.backoff import backoff
from google.api_core.exceptions import TooManyRequests
from google.cloud import storage


class GCSObjectStore(ObjectStore):
    def __init__(self, bucket, client=None):
        self.bucket = check.str_param(bucket, "bucket")
        self.client = client or storage.Client()
        self.bucket_obj = self.client.get_bucket(bucket)
        assert self.bucket_obj.exists()
        super(GCSObjectStore, self).__init__("gs", sep="/")

    def set_object(self, key, obj, serialization_strategy=None):
        check.str_param(key, "key")

        logging.info("Writing GCS object at: " + self.uri_for_key(key))

        # cannot check obj since could be arbitrary Python object
        check.inst_param(
            serialization_strategy, "serialization_strategy", SerializationStrategy
        )  # cannot be none here

        if self.has_object(key):
            logging.warning("Removing existing GCS key: {key}".format(key=key))
            backoff(self.rm_object, args=[key], retry_on=(TooManyRequests,))

        with (
            BytesIO()
            if serialization_strategy.write_mode == "wb" or sys.version_info < (3, 0)
            else StringIO()
        ) as file_like:
            serialization_strategy.serialize(obj, file_like)
            file_like.seek(0)
            backoff(
                self.bucket_obj.blob(key).upload_from_file,
                args=[file_like],
                retry_on=(TooManyRequests,),
            )

        return self.uri_for_key(key)

    def get_object(self, key, serialization_strategy=None):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")
        check.inst_param(
            serialization_strategy, "serialization_strategy", SerializationStrategy
        )  # cannot be none here

        if serialization_strategy.read_mode == "rb":
            file_obj = BytesIO()
            self.bucket_obj.blob(key).download_to_file(file_obj)
        else:
            file_obj = StringIO(
                self.bucket_obj.blob(key)
                .download_as_string()
                .decode(serialization_strategy.encoding)
            )

        file_obj.seek(0)

        obj = serialization_strategy.deserialize(file_obj)
        return obj, self.uri_for_key(key)

    def has_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")
        blobs = self.client.list_blobs(self.bucket, prefix=key)
        return len(list(blobs)) > 0

    def rm_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")

        if self.bucket_obj.blob(key).exists():
            self.bucket_obj.blob(key).delete()

        return self.uri_for_key(key)

    def cp_object(self, src, dst):
        check.str_param(src, "src")
        check.str_param(dst, "dst")

        source_blob = self.bucket_obj.blob(src)
        self.bucket_obj.copy_blob(source_blob, self.bucket_obj, dst)

        return (
            self.uri_for_key(src),
            self.uri_for_key(dst),
        )

    def uri_for_key(self, key, protocol=None):
        check.str_param(key, "key")
        protocol = check.opt_str_param(protocol, "protocol", default="gs://")
        return protocol + self.bucket + "/" + "{key}".format(key=key)
