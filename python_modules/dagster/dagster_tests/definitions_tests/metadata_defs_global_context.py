from dagster._core.definitions.asset_spec import AssetSpec
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.definitions_loader import DefinitionsLoadContext, DefinitionsLoadType
from dagster._core.definitions.external_asset import external_assets_from_specs

from dagster_tests.definitions_tests.test_definitions_loader import fetch_foo_integration_asset_info

FOO_INTEGRATION_SOURCE_KEY = "foo_integration"

WORKSPACE_ID = "my_workspace"


# This function would be provided by integration lib dagster-foo
def _get_foo_integration_defs(workspace_id: str) -> Definitions:
    context = DefinitionsLoadContext.get()
    metadata_key = f"{FOO_INTEGRATION_SOURCE_KEY}/{workspace_id}"
    if (
        context.load_type == DefinitionsLoadType.RECONSTRUCTION
        and metadata_key in context.reconstruction_metadata
    ):
        payload = context.reconstruction_metadata[metadata_key]
    else:
        payload = fetch_foo_integration_asset_info(workspace_id)
    asset_specs = [AssetSpec(item["id"]) for item in payload]
    assets = external_assets_from_specs(asset_specs)
    return Definitions(
        assets=assets,
    ).with_reconstruction_metadata({metadata_key: payload})


@asset
def regular_asset(): ...


defs = Definitions.merge(
    _get_foo_integration_defs(WORKSPACE_ID),
    Definitions(assets=[regular_asset]),
)
