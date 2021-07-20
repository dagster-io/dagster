import pytest
from dagster import AssetKey, DagsterInvalidDefinitionError, SolidDefinition
from dagster.core.asset_defs import asset


def test_asset_no_decorator_args():
    @asset
    def my_asset():
        return 1

    assert isinstance(my_asset, SolidDefinition)
    assert len(my_asset.output_defs) == 1
    assert len(my_asset.input_defs) == 0


def test_asset_with_inputs():
    @asset
    def my_asset(arg1):
        return arg1

    assert isinstance(my_asset, SolidDefinition)
    assert len(my_asset.output_defs) == 1
    assert len(my_asset.input_defs) == 1
    assert my_asset.input_defs[0].metadata["logical_asset_key"] == AssetKey("arg1")


def test_asset_with_inputs_and_namespace():
    @asset(namespace="my_namespace")
    def my_asset(arg1):
        return arg1

    assert isinstance(my_asset, SolidDefinition)
    assert len(my_asset.output_defs) == 1
    assert len(my_asset.input_defs) == 1
    assert my_asset.input_defs[0].metadata["logical_asset_key"] == AssetKey(
        ["my_namespace", "arg1"]
    )


def test_asset_with_context_arg():
    @asset
    def my_asset(context):
        context.log("hello")

    assert isinstance(my_asset, SolidDefinition)
    assert len(my_asset.input_defs) == 0


def test_asset_with_context_arg_and_dep():
    @asset
    def my_asset(context, arg1):
        context.log("hello")
        assert arg1

    assert isinstance(my_asset, SolidDefinition)
    assert len(my_asset.input_defs) == 1
    assert my_asset.input_defs[0].metadata["logical_asset_key"] == AssetKey("arg1")


def test_all_fields():
    @asset(
        required_resource_keys={"abc", "123"},
        io_manager_key="my_io_key",
        description="some description",
        metadata={"metakey": "metaval"},
    )
    def my_asset():
        pass

    assert my_asset.required_resource_keys == {"abc", "123"}
    assert my_asset.description == "some description"
    assert len(my_asset.output_defs) == 1
    output_def = my_asset.output_defs[0]
    assert output_def.io_manager_key == "my_io_key"
    assert output_def.metadata["metakey"] == "metaval"


def test_banned_metadata_keys():
    with pytest.raises(DagsterInvalidDefinitionError):

        @asset(metadata={"logical_asset_key": 123})
        def _asset():
            pass

    with pytest.raises(DagsterInvalidDefinitionError):

        @asset(metadata={"namespace": 123})
        def _asset2():
            pass
