from dagster import AssetKey, Out, Output
from dagster.core.asset_defs import AssetIn, SourceAsset, asset, multi_asset


def test_with_replaced_asset_keys():
    @asset(ins={"input2": AssetIn(namespace="something_else")})
    def asset1(input1, input2):
        assert input1
        assert input2

    replaced = asset1.with_replaced_asset_keys(
        output_asset_key_replacements={
            AssetKey(["asset1"]): AssetKey(["prefix1", "asset1_changed"])
        },
        input_asset_key_replacements={
            AssetKey(["something_else", "input2"]): AssetKey(["apple", "banana"])
        },
    )

    assert set(replaced.dependency_asset_keys) == {
        AssetKey("input1"),
        AssetKey(["apple", "banana"]),
    }
    assert replaced.asset_keys == {AssetKey(["prefix1", "asset1_changed"])}

    assert replaced.asset_keys_by_input_name["input1"] == AssetKey("input1")

    assert replaced.asset_keys_by_input_name["input2"] == AssetKey(["apple", "banana"])

    assert replaced.asset_keys_by_output_name["result"] == AssetKey(["prefix1", "asset1_changed"])


def test_to_source_assets():
    @asset(metadata={"a": "b"}, io_manager_key="abc", description="blablabla")
    def my_asset():
        ...

    assert my_asset.to_source_assets() == [
        SourceAsset(
            AssetKey(["my_asset"]),
            metadata={"a": "b"},
            io_manager_key="abc",
            description="blablabla",
        )
    ]

    @multi_asset(
        outs={
            "my_out_name": Out(
                asset_key=AssetKey("my_asset_name"),
                metadata={"a": "b"},
                io_manager_key="abc",
                description="blablabla",
            ),
            "my_other_out_name": Out(
                asset_key=AssetKey("my_other_asset"),
                metadata={"c": "d"},
                io_manager_key="def",
                description="ablablabl",
            ),
        }
    )
    def my_multi_asset():
        yield Output(1, "my_out_name")
        yield Output(2, "my_other_out_name")

    assert my_multi_asset.to_source_assets() == [
        SourceAsset(
            AssetKey(["my_asset_name"]),
            metadata={"a": "b"},
            io_manager_key="abc",
            description="blablabla",
        ),
        SourceAsset(
            AssetKey(["my_other_asset"]),
            metadata={"c": "d"},
            io_manager_key="def",
            description="ablablabl",
        ),
    ]
