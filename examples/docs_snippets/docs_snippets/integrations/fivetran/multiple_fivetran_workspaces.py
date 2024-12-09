from dagster_fivetran import FivetranWorkspace, load_fivetran_asset_specs

import dagster as dg

sales_fivetran_workspace = FivetranWorkspace(
    account_id=dg.EnvVar("FIVETRAN_SALES_ACCOUNT_ID"),
    api_key=dg.EnvVar("FIVETRAN_SALES_API_KEY"),
    api_secret=dg.EnvVar("FIVETRAN_SALES_API_SECRET"),
)
marketing_fivetran_workspace = FivetranWorkspace(
    account_id=dg.EnvVar("FIVETRAN_MARKETING_ACCOUNT_ID"),
    api_key=dg.EnvVar("FIVETRAN_MARKETING_API_KEY"),
    api_secret=dg.EnvVar("FIVETRAN_MARKETING_API_SECRET"),
)

sales_fivetran_specs = load_fivetran_asset_specs(sales_fivetran_workspace)
marketing_fivetran_specs = load_fivetran_asset_specs(marketing_fivetran_workspace)

# Merge the specs into a single set of definitions
defs = dg.Definitions(
    assets=[*sales_fivetran_specs, *marketing_fivetran_specs],
    resources={
        "marketing_fivetran": marketing_fivetran_workspace,
        "sales_fivetran": sales_fivetran_workspace,
    },
)
