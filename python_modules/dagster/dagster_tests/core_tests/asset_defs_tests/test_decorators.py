import pytest
from dagster import AssetKey, DagsterInvalidDefinitionError, String, check, Out, Output
from dagster.core.asset_defs import AssetIn, AssetsDefinition, asset, multi_asset


def test_asset_no_decorator_args():
    @asset
    def my_asset():
        return 1

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 0


def test_asset_with_inputs():
    @asset
    def my_asset(arg1):
        return arg1

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    assert my_asset.op.input_defs[0].get_asset_key(None) == AssetKey("arg1")


def test_asset_with_compute_kind():
    @asset(compute_kind="sql")
    def my_asset(arg1):
        return arg1

    assert my_asset.op.tags == {"kind": "sql"}


def test_multi_asset_with_compute_kind():
    @multi_asset(outs={"o1": Out(asset_key=AssetKey("o1"))}, compute_kind="sql")
    def my_asset(arg1):
        return arg1

    assert my_asset.op.tags == {"kind": "sql"}


def test_multi_asset_out_name_diff_from_asset_key():
    @multi_asset(
        outs={
            "my_out_name": Out(asset_key=AssetKey("my_asset_name")),
            "my_other_out_name": Out(asset_key=AssetKey("my_other_asset")),
        }
    )
    def my_asset():
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    assert my_asset.asset_keys == {AssetKey("my_asset_name"), AssetKey("my_other_asset")}


def test_multi_asset_infer_from_empty_asset_key():
    @multi_asset(outs={"my_out_name": Out(), "my_other_out_name": Out()})
    def my_asset():
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    assert my_asset.asset_keys == {AssetKey("my_out_name"), AssetKey("my_other_out_name")}


def test_asset_with_dagster_type():
    @asset(dagster_type=String)
    def my_asset(arg1):
        return arg1

    assert my_asset.op.output_defs[0].dagster_type.display_name == "String"


def test_asset_with_inputs_and_namespace():
    @asset(namespace="my_namespace")
    def my_asset(arg1):
        return arg1

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.output_defs) == 1
    assert len(my_asset.op.input_defs) == 1
    assert my_asset.op.input_defs[0].get_asset_key(None) == AssetKey(["my_namespace", "arg1"])


def test_asset_with_context_arg():
    @asset
    def my_asset(context):
        context.log("hello")

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.input_defs) == 0


def test_asset_with_context_arg_and_dep():
    @asset
    def my_asset(context, arg1):
        context.log("hello")
        assert arg1

    assert isinstance(my_asset, AssetsDefinition)
    assert len(my_asset.op.input_defs) == 1
    assert my_asset.op.input_defs[0].get_asset_key(None) == AssetKey("arg1")


def test_input_asset_key():
    @asset(ins={"arg1": AssetIn(asset_key=AssetKey("foo"))})
    def my_asset(arg1):
        assert arg1

    assert my_asset.op.input_defs[0].get_asset_key(None) == AssetKey("foo")


def test_input_asset_key_and_namespace():
    with pytest.raises(check.CheckError, match="key and namespace cannot both be set"):

        @asset(ins={"arg1": AssetIn(asset_key=AssetKey("foo"), namespace="bar")})
        def my_asset(arg1):
            assert arg1


def test_input_namespace():
    @asset(ins={"arg1": AssetIn(namespace="abc")})
    def my_asset(arg1):
        assert arg1

    assert my_asset.op.input_defs[0].get_asset_key(None) == AssetKey(["abc", "arg1"])


def test_input_metadata():
    @asset(ins={"arg1": AssetIn(metadata={"abc": 123})})
    def my_asset(arg1):
        assert arg1

    assert my_asset.op.input_defs[0].metadata == {"abc": 123}


def test_unknown_in():
    with pytest.raises(DagsterInvalidDefinitionError):

        @asset(ins={"arg1": AssetIn()})
        def _my_asset():
            pass


def test_all_fields():
    @asset(
        required_resource_keys={"abc", "123"},
        io_manager_key="my_io_key",
        description="some description",
        metadata={"metakey": "metaval"},
    )
    def my_asset():
        pass

    assert my_asset.op.required_resource_keys == {"abc", "123"}
    assert my_asset.op.description == "some description"
    assert len(my_asset.op.output_defs) == 1
    output_def = my_asset.op.output_defs[0]
    assert output_def.io_manager_key == "my_io_key"
    assert output_def.metadata["metakey"] == "metaval"


def test_infer_input_dagster_type():
    @asset
    def my_asset(_input1: str):
        pass

    assert my_asset.op.input_defs[0].dagster_type.display_name == "String"
