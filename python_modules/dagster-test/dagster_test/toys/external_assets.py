from dagster import AssetMaterialization, AssetSpec, Definitions, OpExecutionContext, job, op
from dagster._core.definitions.external_asset import external_assets_from_specs

asset_one = AssetSpec("asset_one")

asset_two = AssetSpec("asset_two", deps=[asset_one])


@op
def insert_materializations(context: OpExecutionContext) -> None:
    context.log_event(
        AssetMaterialization(asset_one.key, metadata={"nrows": 10, "source": "From this script."})
    )
    context.log_event(
        AssetMaterialization(asset_two.key, metadata={"nrows": 12, "source": "From this script."})
    )


@job
def insert_materializations_job() -> None:
    insert_materializations()


defs = Definitions(
    assets=external_assets_from_specs([asset_one, asset_two]), jobs=[insert_materializations_job]
)
