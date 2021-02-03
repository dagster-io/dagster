import os

import pytest
from dagster import (
    Bool,
    Int,
    List,
    Nothing,
    Optional,
    Output,
    String,
    check,
    execute_pipeline,
    pipeline,
    solid,
)
from dagster.core.definitions.events import ObjectStoreOperationType
from dagster.core.errors import DagsterObjectStoreError
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.instance import DagsterInstance
from dagster.core.storage.intermediate_storage import build_fs_intermediate_storage
from dagster.core.storage.type_storage import TypeStoragePlugin, TypeStoragePluginRegistry
from dagster.core.types.dagster_type import String as RuntimeString
from dagster.core.types.dagster_type import create_any_type, resolve_dagster_type
from dagster.core.types.marshal import SerializationStrategy
from dagster.core.utils import make_new_run_id
from dagster.utils import mkdir_p
from dagster.utils.test import yield_empty_pipeline_context


class UppercaseSerializationStrategy(SerializationStrategy):  # pylint: disable=no-init
    def serialize(self, value, write_file_obj):
        return write_file_obj.write(bytes(value.upper().encode("utf-8")))

    def deserialize(self, read_file_obj):
        return read_file_obj.read().decode("utf-8").lower()


class FancyStringFilesystemTypeStoragePlugin(TypeStoragePlugin):  # pylint:disable=no-init
    @classmethod
    def compatible_with_storage_def(cls, _):
        # Not needed for these tests
        raise NotImplementedError()

    @classmethod
    def set_intermediate_object(
        cls, intermediate_storage, context, dagster_type, step_output_handle, value
    ):
        paths = ["intermediates", step_output_handle.step_key, step_output_handle.output_name]
        paths.append(value)
        mkdir_p(os.path.join(intermediate_storage.root, *paths))

    @classmethod
    def get_intermediate_object(
        cls, intermediate_storage, context, dagster_type, step_output_handle
    ):
        paths = ["intermediates", step_output_handle.step_key, step_output_handle.output_name]
        return os.listdir(os.path.join(intermediate_storage.root, *paths))[0]


LowercaseString = create_any_type(
    "LowercaseString", serialization_strategy=UppercaseSerializationStrategy("uppercase")
)


def define_intermediate_storage(type_storage_plugin_registry=None):
    run_id = make_new_run_id()
    instance = DagsterInstance.ephemeral()
    intermediate_storage = build_fs_intermediate_storage(
        instance.intermediates_directory,
        run_id=run_id,
        type_storage_plugin_registry=type_storage_plugin_registry,
    )
    return run_id, instance, intermediate_storage


def test_file_system_intermediate_storage():
    _, _, intermediate_storage = define_intermediate_storage()

    assert (
        intermediate_storage.set_intermediate(None, Int, StepOutputHandle("return_one"), 21).op
        == ObjectStoreOperationType.SET_OBJECT
    )

    assert (
        intermediate_storage.rm_intermediate(None, StepOutputHandle("return_one")).op
        == ObjectStoreOperationType.RM_OBJECT
    )

    assert (
        intermediate_storage.set_intermediate(None, Int, StepOutputHandle("return_one"), 42).op
        == ObjectStoreOperationType.SET_OBJECT
    )

    assert (
        intermediate_storage.get_intermediate(None, Int, StepOutputHandle("return_one")).obj == 42
    )


def test_file_system_intermediate_storage_composite_types():
    _, _, intermediate_storage = define_intermediate_storage()

    assert intermediate_storage.set_intermediate(
        None, List[Bool], StepOutputHandle("return_true_lst"), [True]
    )

    assert intermediate_storage.has_intermediate(None, StepOutputHandle("return_true_lst"))

    assert intermediate_storage.get_intermediate(
        None, List[Bool], StepOutputHandle("return_true_lst")
    ).obj == [True]


def test_file_system_intermediate_storage_with_custom_serializer():
    run_id, instance, intermediate_storage = define_intermediate_storage()
    with yield_empty_pipeline_context(run_id=run_id, instance=instance) as context:
        intermediate_storage.set_intermediate(
            context, LowercaseString, StepOutputHandle("a.b"), "bar"
        )

        with open(
            os.path.join(intermediate_storage.root, "intermediates", "a.b", "result"), "rb"
        ) as fd:
            assert fd.read().decode("utf-8") == "BAR"

        assert intermediate_storage.has_intermediate(context, StepOutputHandle("a.b"))
        assert (
            intermediate_storage.get_intermediate(
                context, LowercaseString, StepOutputHandle("a.b")
            ).obj
            == "bar"
        )


def test_file_system_intermediate_storage_composite_types_with_custom_serializer_for_inner_type():
    run_id, instance, intermediate_storage = define_intermediate_storage()

    with yield_empty_pipeline_context(run_id=run_id, instance=instance) as context:

        intermediate_storage.set_intermediate(
            context, resolve_dagster_type(List[LowercaseString]), StepOutputHandle("baz"), ["list"]
        )
        assert intermediate_storage.has_intermediate(context, StepOutputHandle("baz"))
        assert intermediate_storage.get_intermediate(
            context, resolve_dagster_type(List[Bool]), StepOutputHandle("baz")
        ).obj == ["list"]


def test_file_system_intermediate_storage_with_type_storage_plugin():
    run_id, instance, intermediate_storage = define_intermediate_storage(
        type_storage_plugin_registry=TypeStoragePluginRegistry(
            [(RuntimeString, FancyStringFilesystemTypeStoragePlugin)]
        ),
    )

    with yield_empty_pipeline_context(run_id=run_id, instance=instance) as context:
        try:
            intermediate_storage.set_intermediate(
                context, RuntimeString, StepOutputHandle("obj_name"), "hello"
            )

            assert intermediate_storage.has_intermediate(context, StepOutputHandle("obj_name"))
            assert (
                intermediate_storage.get_intermediate(
                    context, RuntimeString, StepOutputHandle("obj_name")
                )
                == "hello"
            )

        finally:
            intermediate_storage.rm_intermediate(context, StepOutputHandle("obj_name"))


def test_file_system_intermediate_storage_with_composite_type_storage_plugin():
    run_id, _, intermediate_storage = define_intermediate_storage(
        type_storage_plugin_registry=TypeStoragePluginRegistry(
            [(RuntimeString, FancyStringFilesystemTypeStoragePlugin)]
        ),
    )

    with yield_empty_pipeline_context(run_id=run_id) as context:
        with pytest.raises(check.NotImplementedCheckError):
            intermediate_storage.set_intermediate(
                context, resolve_dagster_type(List[String]), StepOutputHandle("obj_name"), ["hello"]
            )

    with yield_empty_pipeline_context(run_id=run_id) as context:
        with pytest.raises(check.NotImplementedCheckError):
            intermediate_storage.set_intermediate(
                context,
                resolve_dagster_type(Optional[String]),
                StepOutputHandle("obj_name"),
                ["hello"],
            )

    with yield_empty_pipeline_context(run_id=run_id) as context:
        with pytest.raises(check.NotImplementedCheckError):
            intermediate_storage.set_intermediate(
                context,
                resolve_dagster_type(List[Optional[String]]),
                StepOutputHandle("obj_name"),
                ["hello"],
            )

    with yield_empty_pipeline_context(run_id=run_id) as context:
        with pytest.raises(check.NotImplementedCheckError):
            intermediate_storage.set_intermediate(
                context,
                resolve_dagster_type(Optional[List[String]]),
                StepOutputHandle("obj_name"),
                ["hello"],
            )


def test_error_message():
    @solid
    def nothing_solid(_):
        yield Output(Nothing)

    @pipeline
    def repro():
        nothing_solid()

    with pytest.raises(DagsterObjectStoreError):
        execute_pipeline(
            repro,
            run_config={"storage": {"filesystem": {}}},
        )
