from dagster import (
    InputDefinition,
    InputManagerDefinition,
    ModeDefinition,
    ObjectManager,
    OutputDefinition,
    PythonObjectDagsterType,
    execute_pipeline,
    pipeline,
    resource,
    solid,
)
from dagster.core.storage.input_manager import input_manager


def test_validate_inputs():
    @input_manager
    def my_loader(_, _resource_config):
        return 5

    @solid(
        input_defs=[
            InputDefinition(
                "input1", dagster_type=PythonObjectDagsterType(int), manager_key="my_loader"
            )
        ]
    )
    def my_solid(_, input1):
        return input1

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_loader": my_loader})])
    def my_pipeline():
        my_solid()

    execute_pipeline(my_pipeline)


def test_root_input_manager():
    @input_manager
    def my_hardcoded_csv_loader(_context, _resource_config):
        return 5

    @solid(input_defs=[InputDefinition("input1", manager_key="my_loader")])
    def solid1(_, input1):
        assert input1 == 5

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_loader": my_hardcoded_csv_loader})])
    def my_pipeline():
        solid1()

    execute_pipeline(my_pipeline)


def test_configurable_root_input_manager():
    @input_manager(config_schema={"base_dir": str}, input_config_schema={"value": int})
    def my_configurable_csv_loader(context, resource_config):
        assert resource_config["base_dir"] == "abc"
        return context.input_config["value"]

    @solid(input_defs=[InputDefinition("input1", manager_key="my_loader")])
    def solid1(_, input1):
        assert input1 == 5

    @pipeline(mode_defs=[ModeDefinition(resource_defs={"my_loader": my_configurable_csv_loader})])
    def my_configurable_pipeline():
        solid1()

    execute_pipeline(
        my_configurable_pipeline,
        run_config={
            "solids": {"solid1": {"inputs": {"input1": {"value": 5}}}},
            "resources": {"my_loader": {"config": {"base_dir": "abc"}}},
        },
    )


def test_override_object_manager():
    metadata = {"name": 5}

    class MyObjectManager(ObjectManager):
        def handle_output(self, context, obj):
            pass

        def load_input(self, context):
            assert False, "should not be called"

    @resource
    def my_object_manager(_):
        return MyObjectManager()

    @solid(
        output_defs=[
            OutputDefinition(name="my_output", manager_key="my_object_manager", metadata=metadata)
        ]
    )
    def solid1(_):
        return 1

    @solid(input_defs=[InputDefinition("input1", manager_key="spark_loader")])
    def solid2(_, input1):
        assert input1 == 5

    @input_manager
    def spark_table_loader(context, _resource_config):
        output = context.upstream_output
        assert output.metadata == metadata
        assert output.name == "my_output"
        assert output.step_key == "solid1"
        assert context.pipeline_name == "my_pipeline"
        assert context.solid_def.name == solid2.name
        return 5

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "my_object_manager": my_object_manager,
                    "spark_loader": spark_table_loader,
                }
            )
        ]
    )
    def my_pipeline():
        solid2(solid1())

    execute_pipeline(my_pipeline)


def test_configured():
    @input_manager(
        config_schema={"base_dir": str},
        description="abc",
        input_config_schema={"format": str},
        required_resource_keys={"r1", "r2"},
        version="123",
    )
    def my_input_manager(_):
        pass

    configured_input_manager = my_input_manager.configured({"base_dir": "/a/b/c"})

    assert isinstance(configured_input_manager, InputManagerDefinition)
    assert configured_input_manager.description == my_input_manager.description
    assert configured_input_manager.input_config_schema == my_input_manager.input_config_schema
    assert (
        configured_input_manager.required_resource_keys == my_input_manager.required_resource_keys
    )
    assert configured_input_manager.version is None
