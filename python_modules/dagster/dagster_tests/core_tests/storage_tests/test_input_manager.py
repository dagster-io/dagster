from dagster import (
    AssetStore,
    InputDefinition,
    ModeDefinition,
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


def test_override_asset_store():
    asset_metadata = {"name": 5}

    class MyAssetStore(AssetStore):
        def set_asset(self, context, obj):
            pass

        def get_asset(self, context):
            assert False, "should not be called"

    @resource
    def my_asset_store(_):
        return MyAssetStore()

    @solid(
        output_defs=[
            OutputDefinition(
                name="my_output", asset_store_key="my_asset_store", asset_metadata=asset_metadata
            )
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
        assert output.metadata == asset_metadata
        assert output.name == "my_output"
        assert output.step_key == "solid1"
        assert context.pipeline_name == "my_pipeline"
        assert context.solid_def.name == solid2.name
        return 5

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={"my_asset_store": my_asset_store, "spark_loader": spark_table_loader}
            )
        ]
    )
    def my_pipeline():
        solid2(solid1())

    execute_pipeline(my_pipeline)
