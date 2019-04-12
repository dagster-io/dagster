import os
import shutil
import tempfile
import uuid

import pytest

from dagster import (
    Bool as Bool_,
    check,
    List as List_,
    String as String_,
    Nullable as Nullable_,
    PipelineDefinition,
    RunConfig,
    seven,
)
from dagster.core.execution import yield_pipeline_execution_context
from dagster.core.types.marshal import SerializationStrategy
from dagster.core.object_store import FileSystemObjectStore, S3ObjectStore, TypeStoragePlugin
from dagster.core.types.runtime import Bool, resolve_to_runtime_type, RuntimeType, String
from dagster.utils import mkdir_p

from ..marks import aws, nettest


class UppercaseSerializationStrategy(SerializationStrategy):  # pylint: disable=no-init
    def serialize_value(self, _context, value, write_file_obj):
        return write_file_obj.write(bytes(value.upper().encode('utf-8')))

    def deserialize_value(self, _context, read_file_obj):
        return read_file_obj.read().decode('utf-8').lower()


class LowercaseString(RuntimeType):
    def __init__(self):
        super(LowercaseString, self).__init__(
            'lowercase_string',
            'LowercaseString',
            serialization_strategy=UppercaseSerializationStrategy(),
        )


class FancyStringFilesystemTypeStoragePlugin(TypeStoragePlugin):  # pylint:disable=no-init
    @classmethod
    def set_object(cls, object_store, obj, context, runtime_type, paths):
        check.inst_param(object_store, 'object_store', FileSystemObjectStore)
        paths.append(obj)
        mkdir_p(os.path.join(object_store.root, *paths))

    @classmethod
    def get_object(cls, object_store, context, runtime_type, paths):
        check.inst_param(object_store, 'object_store', FileSystemObjectStore)
        return os.listdir(os.path.join(object_store.root, *paths))[0]


class FancyStringS3TypeStoragePlugin(TypeStoragePlugin):  # pylint:disable=no-init
    @classmethod
    def set_object(cls, object_store, obj, context, runtime_type, paths):
        check.inst_param(object_store, 'object_store', S3ObjectStore)
        paths.append(obj)
        return object_store.set_object('', context, runtime_type, paths)

    @classmethod
    def get_object(cls, object_store, context, runtime_type, paths):
        check.inst_param(object_store, 'object_store', S3ObjectStore)
        return object_store.s3.list_objects(
            Bucket=object_store.bucket, Prefix=object_store.key_for_paths(paths)
        )['Contents'][0]['Key'].split('/')[-1]


def test_file_system_object_store():
    run_id = str(uuid.uuid4())

    object_store = FileSystemObjectStore(run_id=run_id)
    assert object_store.root == os.path.join(
        seven.get_system_temp_directory(), 'dagster', 'runs', run_id, 'files'
    )

    with yield_pipeline_execution_context(
        PipelineDefinition([]), {}, RunConfig(run_id=run_id)
    ) as context:
        try:
            object_store.set_object(True, context, Bool.inst(), ['true'])
            assert object_store.has_object(context, ['true'])
            assert object_store.get_object(context, Bool.inst(), ['true']) is True
            assert object_store.url_for_paths(['true']).startswith('file:///')
            assert object_store.rm_object(context, ['true']) is None
            assert object_store.rm_object(context, ['true']) is None
            assert object_store.rm_object(context, ['dslkfhjsdflkjfs']) is None
        finally:
            try:
                shutil.rmtree(object_store.root)
            except seven.FileNotFoundError:
                pass


def test_file_system_object_store_with_base_dir():
    run_id = str(uuid.uuid4())

    try:
        tempdir = tempfile.mkdtemp()

        object_store = FileSystemObjectStore(run_id=run_id, base_dir=tempdir)
        assert object_store.root == os.path.join(tempdir, 'dagster', 'runs', run_id, 'files')

        with yield_pipeline_execution_context(
            PipelineDefinition([]), {}, RunConfig(run_id=run_id)
        ) as context:
            try:
                object_store.set_object(True, context, Bool.inst(), ['true'])
                assert object_store.has_object(context, ['true'])
                assert object_store.get_object(context, Bool.inst(), ['true']) is True

            finally:
                try:
                    shutil.rmtree(object_store.root)
                except seven.FileNotFoundError:
                    pass
    finally:
        try:
            shutil.rmtree(tempdir)
        except seven.FileNotFoundError:
            pass


def test_file_system_object_store_composite_types():
    run_id = str(uuid.uuid4())

    object_store = FileSystemObjectStore(run_id=run_id)
    assert object_store.root == os.path.join(
        seven.get_system_temp_directory(), 'dagster', 'runs', run_id, 'files'
    )

    with yield_pipeline_execution_context(
        PipelineDefinition([]), {}, RunConfig(run_id=run_id)
    ) as context:
        try:
            object_store.set_object(
                [True, False], context, resolve_to_runtime_type(List_(Bool_)).inst(), ['bool']
            )
            assert object_store.has_object(context, ['bool'])
            assert object_store.get_object(
                context, resolve_to_runtime_type(List_(Bool_)).inst(), ['bool']
            ) == [True, False]

        finally:
            try:
                shutil.rmtree(object_store.root)
            except seven.FileNotFoundError:
                pass


def test_file_system_object_store_with_custom_serializer():
    run_id = str(uuid.uuid4())

    object_store = FileSystemObjectStore(run_id=run_id)

    with yield_pipeline_execution_context(
        PipelineDefinition([]), {}, RunConfig(run_id=run_id)
    ) as context:
        try:
            object_store.set_object('foo', context, LowercaseString.inst(), ['foo'])

            with open(os.path.join(object_store.root, 'foo'), 'rb') as fd:
                assert fd.read().decode('utf-8') == 'FOO'

            assert object_store.has_object(context, ['foo'])
            assert object_store.get_object(context, LowercaseString.inst(), ['foo']) == 'foo'
        finally:
            try:
                shutil.rmtree(object_store.root)
            except seven.FileNotFoundError:
                pass


def test_file_system_object_store_composite_types_with_custom_serializer_for_inner_type():
    run_id = str(uuid.uuid4())

    object_store = FileSystemObjectStore(run_id=run_id)
    assert object_store.root == os.path.join(
        seven.get_system_temp_directory(), 'dagster', 'runs', run_id, 'files'
    )

    with yield_pipeline_execution_context(
        PipelineDefinition([]), {}, RunConfig(run_id=run_id)
    ) as context:
        try:
            object_store.set_object(
                ['foo', 'bar'],
                context,
                resolve_to_runtime_type(List_(LowercaseString)).inst(),
                ['list'],
            )
            assert object_store.has_object(context, ['list'])
            assert object_store.get_object(
                context, resolve_to_runtime_type(List_(Bool_)).inst(), ['list']
            ) == ['foo', 'bar']

        finally:
            try:
                shutil.rmtree(object_store.root)
            except seven.FileNotFoundError:
                pass


@aws
@nettest
def test_s3_object_store():
    run_id = str(uuid.uuid4())

    # FIXME need a dedicated test bucket
    object_store = S3ObjectStore(run_id=run_id, s3_bucket='dagster-airflow-scratch')
    assert object_store.root == '/'.join(['dagster', 'runs', run_id, 'files'])

    with yield_pipeline_execution_context(
        PipelineDefinition([]), {}, RunConfig(run_id=run_id)
    ) as context:
        try:
            object_store.set_object(True, context, Bool.inst(), ['true'])

            assert object_store.has_object(context, ['true'])
            assert object_store.get_object(context, Bool.inst(), ['true']) is True
            assert object_store.url_for_paths(['true']).startswith('s3://')

        finally:
            object_store.rm_object(context, ['true'])


@aws
@nettest
def test_s3_object_store_with_custom_serializer():
    run_id = str(uuid.uuid4())

    # FIXME need a dedicated test bucket
    object_store = S3ObjectStore(run_id=run_id, s3_bucket='dagster-airflow-scratch')

    with yield_pipeline_execution_context(
        PipelineDefinition([]), {}, RunConfig(run_id=run_id)
    ) as context:
        try:
            object_store.set_object('foo', context, LowercaseString.inst(), ['foo'])

            assert (
                object_store.s3.get_object(
                    Bucket=object_store.bucket, Key='/'.join([object_store.root] + ['foo'])
                )['Body']
                .read()
                .decode('utf-8')
                == 'FOO'
            )

            assert object_store.has_object(context, ['foo'])
            assert object_store.get_object(context, LowercaseString.inst(), ['foo']) == 'foo'
        finally:
            object_store.rm_object(context, ['foo'])


@aws
@nettest
def test_s3_object_store_composite_types_with_custom_serializer_for_inner_type():
    run_id = str(uuid.uuid4())

    object_store = S3ObjectStore(run_id=run_id, s3_bucket='dagster-airflow-scratch')
    with yield_pipeline_execution_context(
        PipelineDefinition([]), {}, RunConfig(run_id=run_id)
    ) as context:
        try:
            object_store.set_object(
                ['foo', 'bar'],
                context,
                resolve_to_runtime_type(List_(LowercaseString)).inst(),
                ['list'],
            )
            assert object_store.has_object(context, ['list'])
            assert object_store.get_object(
                context, resolve_to_runtime_type(List_(Bool_)).inst(), ['list']
            ) == ['foo', 'bar']

        finally:
            object_store.rm_object(context, ['foo'])


def test_file_system_object_store_with_type_storage_plugin():
    run_id = str(uuid.uuid4())

    # FIXME need a dedicated test bucket
    object_store = FileSystemObjectStore(
        run_id=run_id, types_to_register={String.inst(): FancyStringFilesystemTypeStoragePlugin}
    )

    with yield_pipeline_execution_context(
        PipelineDefinition([]), {}, RunConfig(run_id=run_id)
    ) as context:
        try:
            object_store.set_value('hello', context, String.inst(), ['obj_name'])

            assert object_store.has_object(context, ['obj_name'])
            assert object_store.get_value(context, String.inst(), ['obj_name']) == 'hello'

        finally:
            object_store.rm_object(context, ['obj_name'])


def test_file_system_object_store_with_composite_type_storage_plugin():
    run_id = str(uuid.uuid4())

    # FIXME need a dedicated test bucket
    object_store = FileSystemObjectStore(
        run_id=run_id, types_to_register={String.inst(): FancyStringFilesystemTypeStoragePlugin}
    )

    with yield_pipeline_execution_context(
        PipelineDefinition([]), {}, RunConfig(run_id=run_id)
    ) as context:
        with pytest.raises(check.NotImplementedCheckError):
            object_store.set_value(
                ['hello'], context, resolve_to_runtime_type(List_(String_)), ['obj_name']
            )

    with yield_pipeline_execution_context(
        PipelineDefinition([]), {}, RunConfig(run_id=run_id)
    ) as context:
        with pytest.raises(check.NotImplementedCheckError):
            object_store.set_value(
                ['hello'], context, resolve_to_runtime_type(Nullable_(String_)), ['obj_name']
            )

    with yield_pipeline_execution_context(
        PipelineDefinition([]), {}, RunConfig(run_id=run_id)
    ) as context:
        with pytest.raises(check.NotImplementedCheckError):
            object_store.set_value(
                ['hello'], context, resolve_to_runtime_type(List_(Nullable_(String_))), ['obj_name']
            )

    with yield_pipeline_execution_context(
        PipelineDefinition([]), {}, RunConfig(run_id=run_id)
    ) as context:
        with pytest.raises(check.NotImplementedCheckError):
            object_store.set_value(
                ['hello'], context, resolve_to_runtime_type(Nullable_(List_(String_))), ['obj_name']
            )


@aws
@nettest
def test_s3_object_store_with_type_storage_plugin():
    run_id = str(uuid.uuid4())

    # FIXME need a dedicated test bucket
    object_store = S3ObjectStore(
        run_id=run_id,
        s3_bucket='dagster-airflow-scratch',
        types_to_register={String.inst(): FancyStringS3TypeStoragePlugin},
    )

    with yield_pipeline_execution_context(
        PipelineDefinition([]), {}, RunConfig(run_id=run_id)
    ) as context:
        try:
            object_store.set_value('hello', context, String.inst(), ['obj_name'])

            assert object_store.has_object(context, ['obj_name'])
            assert object_store.get_value(context, String.inst(), ['obj_name']) == 'hello'

        finally:
            object_store.rm_object(context, ['obj_name'])


@aws
@nettest
def test_s3_object_store_with_composite_type_storage_plugin():
    run_id = str(uuid.uuid4())

    # FIXME need a dedicated test bucket
    object_store = S3ObjectStore(
        run_id=run_id,
        s3_bucket='dagster-airflow-scratch',
        types_to_register={String.inst(): FancyStringS3TypeStoragePlugin},
    )

    with yield_pipeline_execution_context(
        PipelineDefinition([]), {}, RunConfig(run_id=run_id)
    ) as context:
        with pytest.raises(check.NotImplementedCheckError):
            object_store.set_value(
                ['hello'], context, resolve_to_runtime_type(List_(String_)), ['obj_name']
            )
