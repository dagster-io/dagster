import pytest
from dagster import (
    AssetMaterialization,
    DagsterInvalidDefinitionError,
    DagsterType,
    InputDefinition,
    ModeDefinition,
    Output,
    OutputDefinition,
    OutputManagerDefinition,
    dagster_type_materializer,
    execute_pipeline,
    pipeline,
    solid,
)
from dagster.core.storage.input_manager import input_manager
from dagster.core.storage.output_manager import output_manager


def test_output_manager():
    adict = {}

    @output_manager
    def my_output_manager(_context, _resource_config, obj):
        adict["result"] = obj

    @solid(output_defs=[OutputDefinition(manager_key="my_output_manager")])
    def my_solid(_):
        return 5

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_output_manager": my_output_manager})])
    def my_pipeline():
        my_solid()

    execute_pipeline(my_pipeline)

    assert adict["result"] == 5


def test_configurable_output_manager():
    adict = {}

    @output_manager(output_config_schema=str)
    def my_output_manager(context, _resource_config, obj):
        adict["result"] = (context.config, obj)

    @solid(output_defs=[OutputDefinition(name="my_output", manager_key="my_output_manager")])
    def my_solid(_):
        return 5

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_output_manager": my_output_manager})])
    def my_pipeline():
        my_solid()

    execute_pipeline(
        my_pipeline, run_config={"solids": {"my_solid": {"outputs": {"my_output": "a"}}}}
    )

    assert adict["result"] == ("a", 5)


@pytest.mark.xfail(
    reason="""This test fails during the intermediate state we're in where output managers have
        been introduced, but they haven't yet been consolidated with asset stores. After the
        consolidation, there will be no more asset store attached to the output of my_solid."""
)
def test_output_manager_no_input_manager():
    adict = {}

    @output_manager
    def my_output_manager(_context, _resource_config, obj):
        adict["result"] = obj

    @solid(output_defs=[OutputDefinition(manager_key="my_output_manager")])
    def my_solid(_):
        return 5

    @solid
    def my_downstream_solid(_, input1):
        return input1 + 1

    with pytest.raises(DagsterInvalidDefinitionError):

        @pipeline(
            mode_defs=[ModeDefinition(resource_defs={"my_output_manager": my_output_manager})]
        )
        def my_pipeline():
            my_downstream_solid(my_solid())

        assert my_pipeline


def test_separate_output_manager_input_manager():
    adict = {}

    @output_manager
    def my_output_manager(_context, _resource_config, obj):
        adict["result"] = obj

    @input_manager
    def my_input_manager(_context, _resource_config):
        return adict["result"]

    @solid(output_defs=[OutputDefinition(manager_key="my_output_manager")])
    def my_solid(_):
        return 5

    @solid(input_defs=[InputDefinition("input1", manager_key="my_input_manager")])
    def my_downstream_solid(_, input1):
        return input1 + 1

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "my_input_manager": my_input_manager,
                    "my_output_manager": my_output_manager,
                }
            )
        ]
    )
    def my_pipeline():
        my_downstream_solid(my_solid())

    execute_pipeline(my_pipeline)

    assert adict["result"] == 5


def test_type_materializer_and_configurable_output_manager():
    @dagster_type_materializer(config_schema={"type_materializer_path": str})
    def my_materializer(_, _config, _value):
        assert False, "shouldn't get here"

    adict = {}

    @output_manager(output_config_schema={"output_manager_path": str})
    def my_output_manager(_context, _resource_config, obj):
        adict["result"] = obj

    my_type = DagsterType(lambda _, _val: True, name="my_type", materializer=my_materializer)

    @solid(
        output_defs=[
            OutputDefinition(name="output1", manager_key="my_output_manager", dagster_type=my_type),
            OutputDefinition(name="output2", dagster_type=my_type),
        ]
    )
    def my_solid(_):
        yield Output(5, "output1")
        yield Output(7, "output2")

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_output_manager": my_output_manager})])
    def my_pipeline():
        my_solid()

    execute_pipeline(
        my_pipeline,
        run_config={"solids": {"my_solid": {"outputs": {"output1": {"output_manager_path": "a"}}}}},
    )

    assert adict["result"] == 5


def test_type_materializer_and_nonconfigurable_output_manager():
    adict = {}

    @dagster_type_materializer(config_schema={"type_materializer_path": str})
    def my_materializer(_, _config, _value):
        adict["materialized"] = True
        return AssetMaterialization(asset_key="a")

    @output_manager
    def my_output_manager(_context, _resource_config, obj):
        adict["result"] = obj

    my_type = DagsterType(lambda _, _val: True, name="my_type", materializer=my_materializer)

    @solid(
        output_defs=[
            OutputDefinition(name="output1", manager_key="my_output_manager", dagster_type=my_type),
            OutputDefinition(name="output2", dagster_type=my_type),
        ]
    )
    def my_solid(_):
        yield Output(5, "output1")
        yield Output(7, "output2")

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_output_manager": my_output_manager})])
    def my_pipeline():
        my_solid()

    execute_pipeline(
        my_pipeline,
        run_config={
            "solids": {"my_solid": {"outputs": [{"output1": {"type_materializer_path": "a"}}]}}
        },
    )

    assert adict["result"] == 5
    assert adict["materialized"]


def test_configured():
    @output_manager(
        config_schema={"base_dir": str},
        description="abc",
        output_config_schema={"format": str},
        required_resource_keys={"r1", "r2"},
        version="123",
    )
    def my_output_manager(_):
        pass

    configured_output_manager = my_output_manager.configured({"base_dir": "/a/b/c"})

    assert isinstance(configured_output_manager, OutputManagerDefinition)
    assert configured_output_manager.description == my_output_manager.description
    assert configured_output_manager.output_config_schema == my_output_manager.output_config_schema
    assert (
        configured_output_manager.required_resource_keys == my_output_manager.required_resource_keys
    )
    assert configured_output_manager.version is None
