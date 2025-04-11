from dagster_fivetran import FivetranWorkspace, fivetran_assets

import dagster as dg

fivetran_workspace = FivetranWorkspace(
    account_id=dg.EnvVar("FIVETRAN_ACCOUNT_ID"),
    api_key=dg.EnvVar("FIVETRAN_API_KEY"),
    api_secret=dg.EnvVar("FIVETRAN_API_SECRET"),
)


# start_downstream_asset
@fivetran_assets(
    # Replace with your connector ID
    connector_id="fivetran_connector_id",
    workspace=fivetran_workspace,
)
def fivetran_connector_assets(
    context: dg.AssetExecutionContext, fivetran: FivetranWorkspace
): ...


my_fivetran_table_asset_key = next(
    iter(
        [
            spec.key
            for spec in fivetran_connector_assets.specs
            if spec.metadata.get("dagster/table_name")
            == "my_database.my_schema.my_fivetran_table"
        ]
    )
)


@dg.asset(deps=[my_fivetran_table_asset_key])
def my_downstream_asset(): ...


# end_downstream_asset
