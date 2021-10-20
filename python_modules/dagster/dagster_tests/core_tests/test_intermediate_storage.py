import os

from dagster import Bool, Int, List
from dagster.core.definitions.events import ObjectStoreOperationType
from dagster.core.execution.plan.outputs import StepOutputHandle
from dagster.core.instance import DagsterInstance
from dagster.core.storage.intermediate_storage import build_fs_intermediate_storage
from dagster.core.types.dagster_type import create_any_type, resolve_dagster_type
from dagster.core.types.marshal import SerializationStrategy
from dagster.core.utils import make_new_run_id
from dagster.utils.test import yield_empty_pipeline_context


class UppercaseSerializationStrategy(SerializationStrategy):  # pylint: disable=no-init
    def serialize(self, value, write_file_obj):
        return write_file_obj.write(bytes(value.upper().encode("utf-8")))

    def deserialize(self, read_file_obj):
        return read_file_obj.read().decode("utf-8").lower()


LowercaseString = create_any_type(
    "LowercaseString", serialization_strategy=UppercaseSerializationStrategy("uppercase")
)


def define_intermediate_storage():
    run_id = make_new_run_id()
    instance = DagsterInstance.ephemeral()
    intermediate_storage = build_fs_intermediate_storage(
        instance.intermediates_directory,
        run_id=run_id,
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
