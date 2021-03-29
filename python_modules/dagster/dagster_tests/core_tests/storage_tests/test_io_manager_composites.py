from dagster import (
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    composite_solid,
    execute_pipeline,
    pipeline,
    solid,
)
from dagster.core.storage.io_manager import IOManager, io_manager


def named_io_manager(storage_dict, name):
    @io_manager
    def my_io_manager(_):
        class MyIOManager(IOManager):
            def handle_output(self, context, obj):
                storage_dict[tuple(context.get_run_scoped_output_identifier())] = {
                    "value": obj,
                    "output_manager_name": name,
                }

            def load_input(self, context):
                result = storage_dict[
                    tuple(context.upstream_output.get_run_scoped_output_identifier())
                ]
                return {**result, "input_manager_name": name}

        return MyIOManager()

    return my_io_manager


def test_composite_solid_output():
    """Is the io_manager_key on the inner or outer solid used for storing outputs?"""

    @solid(output_defs=[OutputDefinition(io_manager_key="inner_manager")])
    def my_solid(_):
        return 5

    @solid(
        input_defs=[InputDefinition("x")],
        output_defs=[OutputDefinition(io_manager_key="inner_manager")],
    )
    def my_solid_takes_input(_, x):
        return x

    @composite_solid(output_defs=[OutputDefinition(io_manager_key="outer_manager")])
    def my_composite():
        return my_solid_takes_input(my_solid())

    # Values ingested by inner_manager and outer_manager are stored in storage_dict
    storage_dict = {}

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "inner_manager": named_io_manager(storage_dict, "inner"),
                    "outer_manager": named_io_manager(storage_dict, "outer"),
                },
            )
        ]
    )
    def my_pipeline():
        my_composite()

    result = execute_pipeline(my_pipeline)
    assert result.success
    # Ensure that the IO manager used to store and load my_composite.my_solid_takes_input is the
    # manager of my_solid_takes_input, not my_composite.
    assert storage_dict[(result.run_id, "my_composite.my_solid_takes_input", "result")][
        "value"
    ] == {
        "value": 5,
        "output_manager_name": "inner",
        "input_manager_name": "inner",
    }


def test_composite_solid_upstream_output():
    """Is the io_manager_key on the inner or outer upstream solid used for loading downstream inputs?"""

    @solid(output_defs=[OutputDefinition(io_manager_key="inner_manager")])
    def my_solid(_):
        return 5

    @composite_solid(output_defs=[OutputDefinition(io_manager_key="outer_manager")])
    def my_composite():
        return my_solid()

    @solid
    def downstream_solid(_, input1):
        assert input1 == {
            "value": 5,
            "output_manager_name": "inner",
            "input_manager_name": "inner",
        }

    storage_dict = {}

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "inner_manager": named_io_manager(storage_dict, "inner"),
                    "outer_manager": named_io_manager(storage_dict, "outer"),
                }
            )
        ]
    )
    def my_pipeline():
        downstream_solid(my_composite())

    result = execute_pipeline(my_pipeline)
    assert result.success
