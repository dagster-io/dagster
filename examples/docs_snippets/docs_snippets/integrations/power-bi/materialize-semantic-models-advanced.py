from dagster_powerbi import (
    PowerBIServicePrincipal,
    PowerBIWorkspace,
    build_semantic_model_refresh_asset_definition,
    load_powerbi_asset_specs,
)

import dagster as dg

power_bi_workspace = PowerBIWorkspace(
    credentials=PowerBIServicePrincipal(
        client_id=dg.EnvVar("POWER_BI_CLIENT_ID"),
        client_secret=dg.EnvVar("POWER_BI_CLIENT_SECRET"),
        tenant_id=dg.EnvVar("POWER_BI_TENANT_ID"),
    ),
    workspace_id=dg.EnvVar("POWER_BI_WORKSPACE_ID"),
)


# Asset definition factory which triggers a semantic model refresh and sends a notification
# once complete
def build_semantic_model_refresh_and_notify_asset_def(
    spec: dg.AssetSpec,
) -> dg.AssetsDefinition:
    dataset_id = spec.metadata["dagster-powerbi/id"]

    @dg.multi_asset(specs=[spec], name=spec.key.to_python_identifier())
    def rebuild_semantic_model(
        context: dg.AssetExecutionContext, power_bi: PowerBIWorkspace
    ) -> None:
        power_bi.trigger_and_poll_refresh(dataset_id)
        # Do some custom work after refreshing here, such as sending an email notification

    return rebuild_semantic_model


# Load Power BI asset specs, and use our custom asset definition builder to
# construct a definition for each semantic model
power_bi_assets = [
    build_semantic_model_refresh_and_notify_asset_def(spec=spec)
    if spec.tags.get("dagster-powerbi/asset_type") == "semantic_model"
    else spec
    for spec in load_powerbi_asset_specs(power_bi_workspace)
]
defs = dg.Definitions(
    assets=[*power_bi_assets], resources={"power_bi": power_bi_workspace}
)
