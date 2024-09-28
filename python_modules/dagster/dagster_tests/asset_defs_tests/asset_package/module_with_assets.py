from dagster import AssetKey, SourceAsset, asset, graph_asset, op
from dagster._core.definitions.metadata import (
    CodeReferencesMetadataSet,
    CodeReferencesMetadataValue,
    LocalFileCodeReference,
)

# importing this makes it show up twice when we collect everything
from dagster_tests.asset_defs_tests.asset_package.asset_subpackage.another_module_with_assets import (
    miles_davis,
)

assert miles_davis

elvis_presley = SourceAsset(key=AssetKey("elvis_presley"))


@asset(
    metadata={
        **CodeReferencesMetadataSet(
            code_references=CodeReferencesMetadataValue(
                code_references=[LocalFileCodeReference(file_path=__file__, line_number=1)]
            )
        ),
    }
)
def chuck_berry(elvis_presley, miles_davis):
    pass


@op
def one():
    return 1


@op
def multiply_by_two(input_num):
    return input_num * 2


@graph_asset
def graph_backed_asset():
    return multiply_by_two(one())
