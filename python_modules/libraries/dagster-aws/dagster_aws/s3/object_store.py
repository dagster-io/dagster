import logging
import sys
from io import BytesIO, StringIO

from dagster import check
from dagster.core.storage.object_store import ObjectStore
from dagster.core.types.marshal import SerializationStrategy

from .utils import construct_s3_client


class S3ObjectStore(ObjectStore):
    def __init__(self, bucket, s3_session=None):
        self.bucket = check.str_param(bucket, "bucket")

        self.s3 = s3_session or construct_s3_client(max_attempts=5)
        self.s3.head_bucket(Bucket=bucket)
        super(S3ObjectStore, self).__init__("s3", sep="/")

    def set_object(self, key, obj, serialization_strategy=None):
        check.str_param(key, "key")

        logging.info("Writing S3 object at: " + self.uri_for_key(key))

        # cannot check obj since could be arbitrary Python object
        check.inst_param(
            serialization_strategy, "serialization_strategy", SerializationStrategy
        )  # cannot be none here

        if self.has_object(key):
            logging.warning("Removing existing S3 key: {key}".format(key=key))
            self.rm_object(key)

        with BytesIO() as bytes_io:
            if serialization_strategy.write_mode == "w" and sys.version_info >= (3, 0):
                with StringIO() as string_io:
                    string_io = StringIO()
                    serialization_strategy.serialize(obj, string_io)
                    string_io.seek(0)
                    bytes_io.write(string_io.read().encode("utf-8"))
            else:
                serialization_strategy.serialize(obj, bytes_io)
            bytes_io.seek(0)
            self.s3.put_object(Bucket=self.bucket, Key=key, Body=bytes_io)

        return self.uri_for_key(key)

    def get_object(self, key, serialization_strategy=None):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")
        check.inst_param(
            serialization_strategy, "serialization_strategy", SerializationStrategy
        )  # cannot be none here

        # FIXME we need better error handling for object store
        obj = serialization_strategy.deserialize(
            BytesIO(self.s3.get_object(Bucket=self.bucket, Key=key)["Body"].read())
            if serialization_strategy.read_mode == "rb"
            else StringIO(
                self.s3.get_object(Bucket=self.bucket, Key=key)["Body"]
                .read()
                .decode(serialization_strategy.encoding)
            )
        )

        return obj, self.uri_for_key(key)

    def has_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")

        key_count = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=key)["KeyCount"]
        return bool(key_count > 0)

    def rm_object(self, key):
        check.str_param(key, "key")
        check.param_invariant(len(key) > 0, "key")

        def delete_for_results(store, results):
            store.s3.delete_objects(
                Bucket=store.bucket,
                Delete={"Objects": [{"Key": result["Key"]} for result in results["Contents"]]},
            )

        if self.has_object(key):
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

        return self.uri_for_key(key)

    def cp_object(self, src, dst):
        check.str_param(src, "src")
        check.str_param(dst, "dst")

        self.s3.copy_object(
            Bucket=self.bucket, Key=dst, CopySource={"Bucket": self.bucket, "Key": src}
        )

        return (
            self.uri_for_key(src),
            self.uri_for_key(dst),
        )

    def uri_for_key(self, key, protocol=None):
        check.str_param(key, "key")
        protocol = check.opt_str_param(protocol, "protocol", default="s3://")
        return protocol + self.bucket + "/" + "{key}".format(key=key)
