import os
import shutil
import uuid

from dagster import PipelineDefinition, RunConfig, seven
from dagster.core.execution import yield_pipeline_execution_context
from dagster.core.types.marshal import SerializationStrategy
from dagster.core.object_store import FileSystemObjectStore, S3ObjectStore
from dagster.core.types.runtime import Bool, RuntimeType

from ..marks import aws, nettest


class UppercaseSerializationStrategy(SerializationStrategy):
    def serialize_value(self, value, write_file_obj):
        return write_file_obj.write(bytes(value.upper().encode('utf-8')))

    def deserialize_value(self, read_file_obj):
        return read_file_obj.read().decode('utf-8').lower()


class LowercaseString(RuntimeType):
    def __init__(self):
        super(LowercaseString, self).__init__(
            'lowercase_string',
            'LowercaseString',
            serialization_strategy=UppercaseSerializationStrategy(),
        )


def test_file_system_object_store():
    run_id = str(uuid.uuid4())

    object_store = FileSystemObjectStore(run_id=run_id)
    assert object_store.root == os.path.join(
        seven.get_system_temp_directory(), 'dagster', 'runs', run_id, 'files'
    )

    try:
        with yield_pipeline_execution_context(
            PipelineDefinition([]), {}, RunConfig(run_id=run_id)
        ) as context:
            object_store.set_object(True, context, Bool.inst(), ['true'])

        assert object_store.has_object(context, ['true'])
        assert object_store.get_object(context, Bool.inst(), ['true']) is True
    finally:
        try:
            shutil.rmtree(object_store.root)
        except seven.FileNotFoundError:
            pass


def test_file_system_object_store_with_custom_serializer():
    run_id = str(uuid.uuid4())

    object_store = FileSystemObjectStore(run_id=run_id)

    try:
        with yield_pipeline_execution_context(
            PipelineDefinition([]), {}, RunConfig(run_id=run_id)
        ) as context:
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


@aws
@nettest
def test_s3_object_store():
    run_id = str(uuid.uuid4())

    # FIXME need a dedicated test bucket
    object_store = S3ObjectStore(run_id=run_id, s3_bucket='dagster-airflow-scratch')
    assert object_store.root == '/'.join(['dagster', 'runs', run_id, 'files'])

    try:
        with yield_pipeline_execution_context(
            PipelineDefinition([]), {}, RunConfig(run_id=run_id)
        ) as context:
            object_store.set_object(True, context, Bool.inst(), ['true'])

        assert object_store.has_object(context, ['true'])
        assert object_store.get_object(context, Bool.inst(), ['true']) is True

    finally:
        object_store.rm_object(context, ['true'])


@aws
@nettest
def test_s3_object_store_with_custom_serializer():
    run_id = str(uuid.uuid4())

    # FIXME need a dedicated test bucket
    object_store = S3ObjectStore(run_id=run_id, s3_bucket='dagster-airflow-scratch')

    try:
        with yield_pipeline_execution_context(
            PipelineDefinition([]), {}, RunConfig(run_id=run_id)
        ) as context:
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
        try:
            shutil.rmtree(object_store.root)
        except seven.FileNotFoundError:
            pass
