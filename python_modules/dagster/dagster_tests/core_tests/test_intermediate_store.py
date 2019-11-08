import os
import uuid

import pytest

from dagster import Bool, List, Optional, String, check
from dagster.core.instance import DagsterInstance
from dagster.core.storage.intermediate_store import build_fs_intermediate_store
from dagster.core.storage.type_storage import TypeStoragePlugin, TypeStoragePluginRegistry
from dagster.core.types.marshal import SerializationStrategy
from dagster.core.types.runtime import Bool as RuntimeBool
from dagster.core.types.runtime import RuntimeType
from dagster.core.types.runtime import String as RuntimeString
from dagster.core.types.runtime import resolve_to_runtime_type
from dagster.utils import mkdir_p
from dagster.utils.test import yield_empty_pipeline_context


class UppercaseSerializationStrategy(SerializationStrategy):  # pylint: disable=no-init
    def serialize(self, value, write_file_obj):
        return write_file_obj.write(bytes(value.upper().encode('utf-8')))

    def deserialize(self, read_file_obj):
        return read_file_obj.read().decode('utf-8').lower()


class LowercaseString(RuntimeType):
    def __init__(self):
        super(LowercaseString, self).__init__(
            'lowercase_string',
            'LowercaseString',
            serialization_strategy=UppercaseSerializationStrategy('uppercase'),
        )


class FancyStringFilesystemTypeStoragePlugin(TypeStoragePlugin):  # pylint:disable=no-init
    @classmethod
    def compatible_with_storage_def(cls, _):
        # Not needed for these tests
        raise NotImplementedError()

    @classmethod
    def set_object(cls, intermediate_store, obj, context, runtime_type, paths):
        paths.append(obj)
        mkdir_p(os.path.join(intermediate_store.root, *paths))

    @classmethod
    def get_object(cls, intermediate_store, context, runtime_type, paths):
        return os.listdir(os.path.join(intermediate_store.root, *paths))[0]


def test_file_system_intermediate_store():
    run_id = str(uuid.uuid4())
    instance = DagsterInstance.ephemeral()
    intermediate_store = build_fs_intermediate_store(
        instance.intermediates_directory, run_id=run_id
    )

    with yield_empty_pipeline_context(run_id=run_id, instance=instance) as context:
        intermediate_store.set_object(True, context, RuntimeBool.inst(), ['true'])
        assert intermediate_store.has_object(context, ['true'])
        assert intermediate_store.get_object(context, RuntimeBool.inst(), ['true']).obj is True
        assert intermediate_store.uri_for_paths(['true']).startswith('file:///')
        assert intermediate_store.rm_object(context, ['true']) is None
        assert intermediate_store.rm_object(context, ['true']) is None
        assert intermediate_store.rm_object(context, ['dslkfhjsdflkjfs']) is None


def test_file_system_intermediate_store_composite_types():
    run_id = str(uuid.uuid4())
    instance = DagsterInstance.ephemeral()

    intermediate_store = build_fs_intermediate_store(
        instance.intermediates_directory, run_id=run_id
    )

    with yield_empty_pipeline_context(instance=instance, run_id=run_id) as context:
        intermediate_store.set_object(
            [True, False], context, resolve_to_runtime_type(List[Bool]).inst(), ['bool']
        )
        assert intermediate_store.has_object(context, ['bool'])
        assert intermediate_store.get_object(
            context, resolve_to_runtime_type(List[Bool]).inst(), ['bool']
        ).obj == [True, False]


def test_file_system_intermediate_store_with_custom_serializer():
    run_id = str(uuid.uuid4())
    instance = DagsterInstance.ephemeral()
    intermediate_store = build_fs_intermediate_store(
        instance.intermediates_directory, run_id=run_id
    )

    with yield_empty_pipeline_context(run_id=run_id, instance=instance) as context:

        intermediate_store.set_object('foo', context, LowercaseString.inst(), ['foo'])

        with open(os.path.join(intermediate_store.root, 'foo'), 'rb') as fd:
            assert fd.read().decode('utf-8') == 'FOO'

        assert intermediate_store.has_object(context, ['foo'])
        assert intermediate_store.get_object(context, LowercaseString.inst(), ['foo']).obj == 'foo'


def test_file_system_intermediate_store_composite_types_with_custom_serializer_for_inner_type():
    run_id = str(uuid.uuid4())
    instance = DagsterInstance.ephemeral()
    intermediate_store = build_fs_intermediate_store(
        instance.intermediates_directory, run_id=run_id
    )

    with yield_empty_pipeline_context(run_id=run_id, instance=instance) as context:

        intermediate_store.set_object(
            ['foo', 'bar'], context, resolve_to_runtime_type(List[LowercaseString]).inst(), ['list']
        )
        assert intermediate_store.has_object(context, ['list'])
        assert intermediate_store.get_object(
            context, resolve_to_runtime_type(List[Bool]).inst(), ['list']
        ).obj == ['foo', 'bar']


def test_file_system_intermediate_store_with_type_storage_plugin():
    run_id = str(uuid.uuid4())
    instance = DagsterInstance.ephemeral()

    intermediate_store = build_fs_intermediate_store(
        instance.intermediates_directory,
        run_id=run_id,
        type_storage_plugin_registry=TypeStoragePluginRegistry(
            {RuntimeString.inst(): FancyStringFilesystemTypeStoragePlugin}
        ),
    )

    with yield_empty_pipeline_context(run_id=run_id, instance=instance) as context:
        try:
            intermediate_store.set_value('hello', context, RuntimeString.inst(), ['obj_name'])

            assert intermediate_store.has_object(context, ['obj_name'])
            assert (
                intermediate_store.get_value(context, RuntimeString.inst(), ['obj_name']) == 'hello'
            )

        finally:
            intermediate_store.rm_object(context, ['obj_name'])


def test_file_system_intermediate_store_with_composite_type_storage_plugin():
    run_id = str(uuid.uuid4())

    intermediate_store = build_fs_intermediate_store(
        DagsterInstance.ephemeral().intermediates_directory,
        run_id=run_id,
        type_storage_plugin_registry=TypeStoragePluginRegistry(
            {RuntimeString.inst(): FancyStringFilesystemTypeStoragePlugin}
        ),
    )

    with yield_empty_pipeline_context(run_id=run_id) as context:
        with pytest.raises(check.NotImplementedCheckError):
            intermediate_store.set_value(
                ['hello'], context, resolve_to_runtime_type(List[String]), ['obj_name']
            )

    with yield_empty_pipeline_context(run_id=run_id) as context:
        with pytest.raises(check.NotImplementedCheckError):
            intermediate_store.set_value(
                ['hello'], context, resolve_to_runtime_type(Optional[String]), ['obj_name']
            )

    with yield_empty_pipeline_context(run_id=run_id) as context:
        with pytest.raises(check.NotImplementedCheckError):
            intermediate_store.set_value(
                ['hello'], context, resolve_to_runtime_type(List[Optional[String]]), ['obj_name']
            )

    with yield_empty_pipeline_context(run_id=run_id) as context:
        with pytest.raises(check.NotImplementedCheckError):
            intermediate_store.set_value(
                ['hello'], context, resolve_to_runtime_type(Optional[List[String]]), ['obj_name']
            )
