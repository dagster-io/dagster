import logging

from io import BytesIO

import boto3

from dagster import check
from dagster.core.storage.object_store import ObjectStore
from dagster.core.types.marshal import SerializationStrategy


class S3ObjectStore(ObjectStore):
    def __init__(self, bucket, s3_session=None):
        self.bucket = check.str_param(bucket, 'bucket')
        self.s3 = s3_session or boto3.client('s3')
        self.s3.head_bucket(Bucket=bucket)
        super(S3ObjectStore, self).__init__(sep='/')

    def set_object(self, key, obj, serialization_strategy=None):
        check.str_param(key, 'key')
        # cannot check obj since could be arbitrary Python object
        check.inst_param(
            serialization_strategy, 'serialization_strategy', SerializationStrategy
        )  # cannot be none here

        if self.has_object(key):
            logging.warning('Removing existing S3 key: {key}'.format(key=key))
            self.rm_object(key)

        with BytesIO() as bytes_io:
            serialization_strategy.serialize(obj, bytes_io)
            bytes_io.seek(0)
            self.s3.put_object(Bucket=self.bucket, Key=key, Body=bytes_io)

        return self.uri_for_key(key)

    def get_object(self, key, serialization_strategy=None):
        check.str_param(key, 'key')
        check.param_invariant(len(key) > 0, 'key')

        # FIXME we need better error handling for object store
        return serialization_strategy.deserialize(
            BytesIO(self.s3.get_object(Bucket=self.bucket, Key=key)['Body'].read())
        )

    def has_object(self, key):
        check.str_param(key, 'key')
        check.param_invariant(len(key) > 0, 'key')

        key_count = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=key)['KeyCount']
        return bool(key_count > 0)

    def rm_object(self, key):
        check.str_param(key, 'key')
        check.param_invariant(len(key) > 0, 'key')

        def delete_for_results(store, results):
            store.s3.delete_objects(
                Bucket=store.bucket,
                Delete={'Objects': [{'Key': result['Key']} for result in results['Contents']]},
            )

        if not self.has_object(key):
            return

        results = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=key)
        delete_for_results(self, results)

        continuation = results['IsTruncated']
        while continuation:
            continuation_token = results['NextContinuationToken']
            results = self.s3.list_objects_v2(
                Bucket=self.bucket, Prefix=key, ContinuationToken=continuation_token
            )
            delete_for_results(self, results)
            continuation = results['IsTruncated']

        return

    def cp_object(self, src, dst):
        # https://github.com/dagster-io/dagster/issues/1455
        raise NotImplementedError()

    def uri_for_key(self, key, protocol=None):
        check.str_param(key, 'key')
        protocol = check.opt_str_param(protocol, 'protocol', default='s3://')
        return protocol + self.bucket + '/' + '{key}'.format(key=key)
