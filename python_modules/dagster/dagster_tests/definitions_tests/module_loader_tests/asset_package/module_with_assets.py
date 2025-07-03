import dagster as dg
from dagster._core.definitions.metadata import CodeReferencesMetadataSet

# importing this makes it show up twice when we collect everything
from dagster_tests.definitions_tests.module_loader_tests.asset_package.asset_subpackage.another_module_with_assets import (
    miles_davis,
)

assert miles_davis

elvis_presley = dg.SourceAsset(key=dg.AssetKey("elvis_presley"))


@dg.asset(
    metadata={
        **CodeReferencesMetadataSet(
            code_references=dg.CodeReferencesMetadataValue(
                code_references=[dg.LocalFileCodeReference(file_path=__file__, line_number=1)]
            )
        ),
    }
)
def chuck_berry(elvis_presley, miles_davis):
    pass


@dg.op
def one():
    return 1


@dg.op
def multiply_by_two(input_num):
    return input_num * 2


@dg.graph_asset
def graph_backed_asset():
    return multiply_by_two(one())


my_spec = dg.AssetSpec("my_asset_spec")
