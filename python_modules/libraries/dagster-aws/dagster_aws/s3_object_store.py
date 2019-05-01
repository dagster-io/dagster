from io import BytesIO

import boto3

from dagster import RunStorageMode, check
from dagster.core.execution_context import SystemPipelineExecutionContext
from dagster.core.types.runtime import resolve_to_runtime_type, RuntimeType
from dagster.core.object_store import ObjectStore


class S3ObjectStore(ObjectStore):
    def __init__(self, s3_bucket, run_id, types_to_register=None):
        check.str_param(run_id, 'run_id')

        self.s3 = boto3.client('s3')
        self.bucket = s3_bucket
        self.run_id = run_id

        self.s3.head_bucket(Bucket=self.bucket)

        self.root = 'dagster/runs/{run_id}/files'.format(run_id=self.run_id)
        self.storage_mode = RunStorageMode.S3

        super(S3ObjectStore, self).__init__(types_to_register)

    def url_for_paths(self, paths, protocol='s3://'):
        return protocol + self.bucket + '/' + self.key_for_paths(paths)

    def key_for_paths(self, paths):
        return '/'.join([self.root] + paths)

    def set_object(self, obj, context, runtime_type, paths):
        check.inst_param(context, 'context', SystemPipelineExecutionContext)
        check.inst_param(runtime_type, 'runtime_type', RuntimeType)
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')

        key = self.key_for_paths(paths)

        check.invariant(
            not self.has_object(context, paths), 'Key already exists: {key}!'.format(key=key)
        )

        with BytesIO() as bytes_io:
            runtime_type.serialization_strategy.serialize_value(context, obj, bytes_io)
            bytes_io.seek(0)
            self.s3.put_object(Bucket=self.bucket, Key=key, Body=bytes_io)

        return 's3://{bucket}/{key}'.format(bucket=self.bucket, key=key)

    def get_object(self, context, runtime_type, paths):
        check.inst_param(context, 'context', SystemPipelineExecutionContext)
        check.inst_param(runtime_type, 'runtime_type', RuntimeType)
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')

        key = self.key_for_paths(paths)

        # FIXME we need better error handling for object store
        return runtime_type.serialization_strategy.deserialize_value(
            context, BytesIO(self.s3.get_object(Bucket=self.bucket, Key=key)['Body'].read())
        )

    def has_object(self, context, paths):  # pylint: disable=unused-argument
        prefix = self.key_for_paths(paths)

        key_count = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)['KeyCount']
        if key_count > 0:
            return True
        return False

    def rm_object(self, context, paths):
        def delete_for_results(object_store, results):
            object_store.s3.delete_objects(
                Bucket=self.bucket,
                Delete={'Objects': [{'Key': result['Key']} for result in results['Contents']]},
            )

        if not self.has_object(context, paths):
            return

        prefix = self.key_for_paths(paths)
        results = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        delete_for_results(self, results)

        continuation = results['IsTruncated']
        while continuation:
            continuation_token = results['NextContinuationToken']
            results = self.s3.list_objects_v2(
                Bucket=self.bucket, Prefix=prefix, ContinuationToken=continuation_token
            )
            delete_for_results(self, results)
            continuation = results['IsTruncated']

        return

    def copy_object_from_prev_run(
        self, context, previous_run_id, paths
    ):  # pylint: disable=unused-argument
        check.not_implemented('not supported: TODO for max. put issue number here')


def get_s3_intermediate(context, s3_bucket, run_id, step_key, dagster_type, output_name='result'):
    object_store = S3ObjectStore(s3_bucket, run_id)
    return object_store.get_object(
        context=context,
        runtime_type=resolve_to_runtime_type(dagster_type),
        paths=get_fs_paths(step_key, output_name),
    )


def has_s3_intermediate(context, s3_bucket, run_id, step_key, output_name='result'):
    object_store = S3ObjectStore(s3_bucket, run_id)
    return object_store.has_object(context=context, paths=get_fs_paths(step_key, output_name))


def rm_s3_intermediate(context, s3_bucket, run_id, step_key, output_name='result'):
    object_store = S3ObjectStore(s3_bucket, run_id)
    return object_store.rm_object(context=context, paths=get_fs_paths(step_key, output_name))


def get_fs_paths(step_key, output_name):
    return ['intermediates', step_key, output_name]
