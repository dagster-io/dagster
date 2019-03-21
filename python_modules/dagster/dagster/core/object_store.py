import os
import pickle
import shutil

from abc import ABCMeta, abstractmethod
from io import BytesIO

import six

from dagster import check, seven
from dagster.utils import mkdir_p

from .execution_context import SystemPipelineExecutionContext
from .types.runtime import RuntimeType


def ensure_boto_requirements():
    try:
        import boto3
        import botocore  # pylint: disable=unused-import
    except ImportError:
        raise check.CheckError(
            'boto3 and botocore must both be available for import in order to make use of '
            'an S3ObjectStore'
        )

    return (boto3, botocore)


@six.add_metaclass(ABCMeta)
class ObjectStore:
    @abstractmethod
    def set_object(self, obj, context, runtime_type, paths):
        pass

    @abstractmethod
    def get_object(self, context, runtime_type, paths):
        pass

    @abstractmethod
    def has_object(self, context, paths):
        pass

    @abstractmethod
    def rm_object(self, context, paths):
        pass


def get_run_files_directory(run_id):
    return os.path.join(seven.get_system_temp_directory(), 'dagster', 'runs', run_id, 'files')


def get_valid_target_path(base_dir, paths):
    if len(paths) > 1:
        target_dir = os.path.join(base_dir, *paths[:-1])
        mkdir_p(target_dir)
        return os.path.join(target_dir, paths[-1])
    else:
        check.invariant(len(paths) == 1)
        target_dir = base_dir
        mkdir_p(target_dir)
        return os.path.join(target_dir, paths[0])


class FileSystemObjectStore(ObjectStore):
    def __init__(self, run_id):
        self.run_id = check.str_param(run_id, 'run_id')
        self.storage_mode = RunStorageMode.FILESYSTEM
        self.root = get_run_files_directory(run_id)

    def set_object(self, obj, context, runtime_type, paths):  # pylint: disable=unused-argument
        check.inst_param(context, 'context', SystemPipelineExecutionContext)
        check.inst_param(runtime_type, 'runtime_type', RuntimeType)
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')

        target_path = get_valid_target_path(self.root, paths)

        check.invariant(not os.path.exists(target_path))
        with open(target_path, 'wb') as ff:
            # Hardcode pickle for now
            pickle.dump(obj, ff)

    def get_object(self, context, runtime_type, paths):  # pylint: disable=unused-argument
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')
        target_path = os.path.join(self.root, *paths)
        with open(target_path, 'rb') as ff:
            return pickle.load(ff)

    def has_object(self, context, paths):  # pylint: disable=unused-argument
        target_path = os.path.join(self.root, *paths)
        return os.path.isfile(target_path)

    def rm_object(self, context, paths):  # pylint: disable=unused-argument
        target_path = os.path.join(self.root, *paths)
        if not self.has_object(context, paths):
            return
        os.unlink(target_path)
        return

    def copy_object_from_prev_run(
        self, context, previous_run_id, paths
    ):  # pylint: disable=unused-argument
        prev_run_files_dir = get_run_files_directory(previous_run_id)
        check.invariant(os.path.isdir(prev_run_files_dir))

        copy_from_path = os.path.join(prev_run_files_dir, *paths)
        copy_to_path = get_valid_target_path(self.root, paths)

        check.invariant(
            not os.path.exists(copy_to_path), 'Path already exists {}'.format(copy_to_path)
        )

        if os.path.isfile(copy_from_path):
            shutil.copy(copy_from_path, copy_to_path)
        elif os.path.isdir(copy_from_path):
            shutil.copytree(copy_from_path, copy_to_path)
        else:
            check.failed('should not get here')


class S3ObjectStore(ObjectStore):
    def __init__(self, s3_bucket, run_id):
        boto3, _ = ensure_boto_requirements()
        check.str_param(run_id, 'run_id')

        self.s3 = boto3.client('s3')
        self.bucket = s3_bucket
        self.run_id = run_id

        self.s3.head_bucket(Bucket=self.bucket)

        self.root = 'dagster/runs/{run_id}/files'.format(run_id=self.run_id)

    def _key_for_paths(self, paths):
        return '/'.join([self.root] + paths)

    def set_object(self, obj, context, runtime_type, paths):
        ensure_boto_requirements()
        check.inst_param(context, 'context', SystemPipelineExecutionContext)
        check.inst_param(runtime_type, 'runtime_type', RuntimeType)
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')

        key = self._key_for_paths(paths)

        check.invariant(
            not self.has_object(context, paths), 'Key already exists: {key}!'.format(key=key)
        )

        with BytesIO() as bytes_io:
            # Hardcode pickle for now
            pickle.dump(obj, bytes_io)
            bytes_io.seek(0)
            self.s3.put_object(Bucket=self.bucket, Key=key, Body=bytes_io)

        return obj

    def get_object(self, context, runtime_type, paths):
        ensure_boto_requirements()
        check.inst_param(context, 'context', SystemPipelineExecutionContext)
        check.inst_param(runtime_type, 'runtime_type', RuntimeType)
        check.list_param(paths, 'paths', of_type=str)
        check.param_invariant(len(paths) > 0, 'paths')

        key = self._key_for_paths(paths)

        return pickle.loads(self.s3.get_object(Bucket=self.bucket, Key=key)['Body'].read())

    def has_object(self, context, paths):  # pylint: disable=unused-argument
        _, botocore = ensure_boto_requirements()
        key = self._key_for_paths(paths)

        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except botocore.exceptions.ClientError as exc:  # pylint: disable=undefined-variable
            if exc.response.get('Error', {}).get('Code') == '404':
                return False
            raise

    def rm_object(self, context, paths):
        ensure_boto_requirements()
        if not self.has_object(context, paths):
            return

        key = self._key_for_paths(paths)
        self.s3.delete_object(Bucket=self.bucket, Key=key)
        return

    def copy_object_from_prev_run(
        self, context, previous_run_id, paths
    ):  # pylint: disable=unused-argument
        check.failed('not supported: TODO for max. put issue number here')


def get_fs_paths(step_key, output_name):
    return ['intermediates', step_key, output_name]


def get_filesystem_intermediate(run_id, step_key, runtime_type, output_name='result'):
    object_store = FileSystemObjectStore(run_id)
    return object_store.get_object(
        context=None, runtime_type=runtime_type, paths=get_fs_paths(step_key, output_name)
    )


def has_filesystem_intermediate(run_id, step_key, output_name='result'):
    object_store = FileSystemObjectStore(run_id)
    return object_store.has_object(context=None, paths=get_fs_paths(step_key, output_name))


def get_s3_intermediate(context, s3_bucket, run_id, step_key, runtime_type, output_name='result'):
    object_store = S3ObjectStore(s3_bucket, run_id)
    return object_store.get_object(
        context=context, runtime_type=runtime_type, paths=get_fs_paths(step_key, output_name)
    )


def has_s3_intermediate(context, s3_bucket, run_id, step_key, output_name='result'):
    object_store = S3ObjectStore(s3_bucket, run_id)
    return object_store.has_object(context=context, paths=get_fs_paths(step_key, output_name))


def rm_s3_intermediate(context, s3_bucket, run_id, step_key, output_name='result'):
    object_store = S3ObjectStore(s3_bucket, run_id)
    return object_store.rm_object(context=context, paths=get_fs_paths(step_key, output_name))
