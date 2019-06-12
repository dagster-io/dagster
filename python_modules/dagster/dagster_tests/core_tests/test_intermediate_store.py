import os
import shutil
import tempfile
import uuid

import pytest

from dagster import check, String, Optional, seven, List, Bool
from dagster.core.storage.intermediate_store import FileSystemIntermediateStore
from dagster.core.storage.type_storage import TypeStoragePlugin, TypeStoragePluginRegistry
from dagster.core.types.marshal import SerializationStrategy
from dagster.core.types.runtime import (
    Bool as RuntimeBool,
    resolve_to_runtime_type,
    RuntimeType,
    String as RuntimeString,
)
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
            serialization_strategy=UppercaseSerializationStrategy(),
        )


class FancyStringFilesystemTypeStoragePlugin(TypeStoragePlugin):  # pylint:disable=no-init
    @classmethod
    def compatible_with_storage_def(cls, _):
        # Not needed for these tests
        raise NotImplementedError()

    @classmethod
    def set_object(cls, intermediate_store, obj, context, runtime_type, paths):
        check.inst_param(intermediate_store, 'intermediate_store', FileSystemIntermediateStore)
        paths.append(obj)
        mkdir_p(os.path.join(intermediate_store.root, *paths))

    @classmethod
    def get_object(cls, intermediate_store, context, runtime_type, paths):
        check.inst_param(intermediate_store, 'intermediate_store', FileSystemIntermediateStore)
        return os.listdir(os.path.join(intermediate_store.root, *paths))[0]


def test_file_system_intermediate_store():
    run_id = str(uuid.uuid4())

    intermediate_store = FileSystemIntermediateStore(run_id=run_id)
    assert intermediate_store.root == os.path.join(
        seven.get_system_temp_directory(), 'dagster', 'runs', run_id, 'files'
    )

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_store.set_object(True, context, RuntimeBool.inst(), ['true'])
            assert intermediate_store.has_object(context, ['true'])
            assert intermediate_store.get_object(context, RuntimeBool.inst(), ['true']) is True
            assert intermediate_store.uri_for_paths(['true']).startswith('file:///')
            assert intermediate_store.rm_object(context, ['true']) is None
            assert intermediate_store.rm_object(context, ['true']) is None
            assert intermediate_store.rm_object(context, ['dslkfhjsdflkjfs']) is None
        finally:
            try:
                shutil.rmtree(intermediate_store.root)
            except seven.FileNotFoundError:
                pass


def test_file_system_intermediate_store_with_base_dir():
    run_id = str(uuid.uuid4())

    try:
        tempdir = tempfile.mkdtemp()

        intermediate_store = FileSystemIntermediateStore(run_id=run_id, base_dir=tempdir)
        assert intermediate_store.root == os.path.join(tempdir, 'dagster', 'runs', run_id, 'files')

        with yield_empty_pipeline_context(run_id=run_id) as context:
            try:
                intermediate_store.set_object(True, context, RuntimeBool.inst(), ['true'])
                assert intermediate_store.has_object(context, ['true'])
                assert intermediate_store.get_object(context, RuntimeBool.inst(), ['true']) is True

            finally:
                try:
                    shutil.rmtree(intermediate_store.root)
                except seven.FileNotFoundError:
                    pass
    finally:
        try:
            shutil.rmtree(tempdir)
        except seven.FileNotFoundError:
            pass


def test_file_system_intermediate_store_composite_types():
    run_id = str(uuid.uuid4())

    intermediate_store = FileSystemIntermediateStore(run_id=run_id)
    assert intermediate_store.root == os.path.join(
        seven.get_system_temp_directory(), 'dagster', 'runs', run_id, 'files'
    )

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_store.set_object(
                [True, False], context, resolve_to_runtime_type(List[Bool]).inst(), ['bool']
            )
            assert intermediate_store.has_object(context, ['bool'])
            assert intermediate_store.get_object(
                context, resolve_to_runtime_type(List[Bool]).inst(), ['bool']
            ) == [True, False]

        finally:
            try:
                shutil.rmtree(intermediate_store.root)
            except seven.FileNotFoundError:
                pass


def test_file_system_intermediate_store_with_custom_serializer():
    run_id = str(uuid.uuid4())

    intermediate_store = FileSystemIntermediateStore(run_id=run_id)

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_store.set_object('foo', context, LowercaseString.inst(), ['foo'])

            with open(os.path.join(intermediate_store.root, 'foo'), 'rb') as fd:
                assert fd.read().decode('utf-8') == 'FOO'

            assert intermediate_store.has_object(context, ['foo'])
            assert intermediate_store.get_object(context, LowercaseString.inst(), ['foo']) == 'foo'
        finally:
            try:
                shutil.rmtree(intermediate_store.root)
            except seven.FileNotFoundError:
                pass


def test_file_system_intermediate_store_composite_types_with_custom_serializer_for_inner_type():
    run_id = str(uuid.uuid4())

    intermediate_store = FileSystemIntermediateStore(run_id=run_id)
    assert intermediate_store.root == os.path.join(
        seven.get_system_temp_directory(), 'dagster', 'runs', run_id, 'files'
    )

    with yield_empty_pipeline_context(run_id=run_id) as context:
        try:
            intermediate_store.set_object(
                ['foo', 'bar'],
                context,
                resolve_to_runtime_type(List[LowercaseString]).inst(),
                ['list'],
            )
            assert intermediate_store.has_object(context, ['list'])
            assert intermediate_store.get_object(
                context, resolve_to_runtime_type(List[Bool]).inst(), ['list']
            ) == ['foo', 'bar']

        finally:
            try:
                shutil.rmtree(intermediate_store.root)
            except seven.FileNotFoundError:
                pass


def test_file_system_intermediate_store_with_type_storage_plugin():
    run_id = str(uuid.uuid4())

    # FIXME need a dedicated test bucket
    intermediate_store = FileSystemIntermediateStore(
        run_id=run_id,
        type_storage_plugin_registry=TypeStoragePluginRegistry(
            {RuntimeString.inst(): FancyStringFilesystemTypeStoragePlugin}
        ),
    )

    with yield_empty_pipeline_context(run_id=run_id) as context:
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

    # FIXME need a dedicated test bucket
    intermediate_store = FileSystemIntermediateStore(
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
