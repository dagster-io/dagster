---
title: "Using Power BI with Dagster"
description: Represent your Power BI assets in Dagster
---

:::

This feature is considered **experimental**

:::

This guide provides instructions for using Dagster with Power BI using the [`dagster-powerbi`](/api/python-api/libraries/dagster-powerbi) library. Your Power BI assets, such as semantic models, data sources, reports, and dashboards, can be represented in the Dagster asset graph, allowing you to track lineage and dependencies between Power BI assets and upstream data assets you are already modeling in Dagster. You can also use Dagster to orchestrate Power BI semantic models, allowing you to trigger refreshes of these models on a cadence or based on upstream data changes.

## What you'll learn

- How to represent Power BI assets in the Dagster asset graph, including lineage to other Dagster assets.
- How to customize asset definition metadata for these Power BI assets.
- How to materialize Power BI semantic models from Dagster.
- How to customize how Power BI semantic models are materialized.

<details>
  <summary>Prerequisites</summary>

- The `dagster` and `dagster-powerbi` libraries installed in your environment
- Familiarity with asset definitions and the Dagster asset graph
- Familiarity with Dagster resources
- Familiarity with Power BI concepts, like semantic models, data sources, reports, and dashboards
- A Power BI workspace
- A service principal configured to access Power BI, or an API access token. For more information, see [Embed Power BI content with service principal and an application secret](https://learn.microsoft.com/en-us/power-bi/developer/embedded/embed-service-principal) in the Power BI documentation.

</details>

## Set up your environment

To get started, you'll need to install the `dagster` and `dagster-powerbi` Python packages:

```bash
pip install dagster dagster-powerbi
```

## Represent Power BI assets in the asset graph

To load Power BI assets into the Dagster asset graph, you must first construct a <PyObject section="libraries" module="dagster_powerbi" object="PowerBIWorkspace" /> resource, which allows Dagster to communicate with your Power BI workspace. You'll need to supply your workspace ID and credentials. You may configure a service principal or use an API access token, which can be passed directly or accessed from the environment using <PyObject section="resources" module="dagster" object="EnvVar" />.

Dagster can automatically load all semantic models, data sources, reports, and dashboards from your Power BI workspace as asset specs. Call the <PyObject section="libraries" module="dagster_powerbi" object="load_powerbi_asset_specs" /> function, which returns a list of <PyObject section="assets" module="dagster" object="AssetSpec" />s representing your Power BI assets. You can then include these asset specs in your <PyObject section="definitions" module="dagster" object="Definitions" /> object:

{/* TODO convert to <CodeExample> */}
```python file=/integrations/power-bi/representing-power-bi-assets.py
from dagster_powerbi import (
    PowerBIServicePrincipal,
    PowerBIToken,
    PowerBIWorkspace,
    load_powerbi_asset_specs,
)

import dagster as dg

# Connect using a service principal
power_bi_workspace = PowerBIWorkspace(
    credentials=PowerBIServicePrincipal(
        client_id=dg.EnvVar("POWER_BI_CLIENT_ID"),
        client_secret=dg.EnvVar("POWER_BI_CLIENT_SECRET"),
        tenant_id=dg.EnvVar("POWER_BI_TENANT_ID"),
    ),
    workspace_id=dg.EnvVar("POWER_BI_WORKSPACE_ID"),
)

# Alternatively, connect directly using an API access token
power_bi_workspace = PowerBIWorkspace(
    credentials=PowerBIToken(api_token=dg.EnvVar("POWER_BI_API_TOKEN")),
    workspace_id=dg.EnvVar("POWER_BI_WORKSPACE_ID"),
)

power_bi_specs = load_powerbi_asset_specs(power_bi_workspace)
defs = dg.Definitions(
    assets=[*power_bi_specs], resources={"power_bi": power_bi_workspace}
)
```

By default, Dagster will attempt to snapshot your entire workspace using Power BI's [metadata scanner APIs](https://learn.microsoft.com/en-us/fabric/governance/metadata-scanning-overview), which are able to retrieve more detailed information about your Power BI assets, but rely on the workspace being configured to allow this access.

If you encounter issues with the scanner APIs, you may disable them using `load_powerbi_asset_specs(power_bi_workspace, use_workspace_scan=False)`.

### Customize asset definition metadata for Power BI assets

By default, Dagster will generate asset specs for each Power BI asset based on its type, and populate default metadata. You can further customize asset properties by passing a custom <PyObject section="libraries" module="dagster_powerbi" object="DagsterPowerBITranslator" /> subclass to the <PyObject section="libraries" module="dagster_powerbi" object="load_powerbi_asset_specs" /> function. This subclass can implement methods to customize the asset specs for each Power BI asset type.

{/* TODO convert to <CodeExample> */}
```python file=/integrations/power-bi/customize-power-bi-asset-defs.py
from dagster_powerbi import (
    DagsterPowerBITranslator,
    PowerBIServicePrincipal,
    PowerBIWorkspace,
    load_powerbi_asset_specs,
)
from dagster_powerbi.translator import PowerBIContentType, PowerBITranslatorData

import dagster as dg

power_bi_workspace = PowerBIWorkspace(
    credentials=PowerBIServicePrincipal(
        client_id=dg.EnvVar("POWER_BI_CLIENT_ID"),
        client_secret=dg.EnvVar("POWER_BI_CLIENT_SECRET"),
        tenant_id=dg.EnvVar("POWER_BI_TENANT_ID"),
    ),
    workspace_id=dg.EnvVar("POWER_BI_WORKSPACE_ID"),
)


# A translator class lets us customize properties of the built
# Power BI assets, such as the owners or asset key
class MyCustomPowerBITranslator(DagsterPowerBITranslator):
    def get_asset_spec(self, data: PowerBITranslatorData) -> dg.AssetSpec:
        # We create the default asset spec using super()
        default_spec = super().get_asset_spec(data)
        # We customize the team owner tag for all assets,
        # and we customize the asset key prefix only for dashboards.
        return default_spec.replace_attributes(
            key=(
                default_spec.key.with_prefix("prefix")
                if data.content_type == PowerBIContentType.DASHBOARD
                else default_spec.key
            ),
            owners=["team:my_team"],
        )


power_bi_specs = load_powerbi_asset_specs(
    power_bi_workspace, dagster_powerbi_translator=MyCustomPowerBITranslator()
)
defs = dg.Definitions(
    assets=[*power_bi_specs], resources={"power_bi": power_bi_workspace}
)
```

Note that `super()` is called in each of the overridden methods to generate the default asset spec. It is best practice to generate the default asset spec before customizing it.

### Load Power BI assets from multiple workspaces

Definitions from multiple Power BI workspaces can be combined by instantiating multiple <PyObject section="libraries" module="dagster_powerbi" object="PowerBIWorkspace" /> resources and merging their specs. This lets you view all your Power BI assets in a single asset graph:

{/* TODO convert to <CodeExample> */}
```python file=/integrations/power-bi/multiple-power-bi-workspaces.py
from dagster_powerbi import (
    PowerBIServicePrincipal,
    PowerBIWorkspace,
    load_powerbi_asset_specs,
)

import dagster as dg

credentials = PowerBIServicePrincipal(
    client_id=dg.EnvVar("POWER_BI_CLIENT_ID"),
    client_secret=dg.EnvVar("POWER_BI_CLIENT_SECRET"),
    tenant_id=dg.EnvVar("POWER_BI_TENANT_ID"),
)

sales_team_workspace = PowerBIWorkspace(
    credentials=credentials,
    workspace_id="726c94ff-c408-4f43-8edf-61fbfa1753c7",
)

marketing_team_workspace = PowerBIWorkspace(
    credentials=credentials,
    workspace_id="8b7f815d-4e64-40dd-993c-cfa4fb12edee",
)

sales_team_specs = load_powerbi_asset_specs(sales_team_workspace)
marketing_team_specs = load_powerbi_asset_specs(marketing_team_workspace)

# Merge the specs into a single set of definitions
defs = dg.Definitions(
    assets=[*sales_team_specs, *marketing_team_specs],
    resources={
        "marketing_power_bi": marketing_team_workspace,
        "sales_power_bi": sales_team_workspace,
    },
)
```

## Materialize Power BI semantic models from Dagster

Dagster's default behavior is to pull in representations of Power BI semantic models as external assets, which appear in the asset graph but can't be materialized. However, you can build executable asset definitions that trigger the refresh of Power BI semantic models. The <PyObject section="libraries" module="dagster_powerbi" object="build_semantic_model_refresh_asset_definition" /> utility will construct an asset definition that triggers a refresh of a semantic model when materialized.

{/* TODO convert to <CodeExample> */}
```python file=/integrations/power-bi/materialize-semantic-models.py
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

# Load Power BI asset specs, and use the asset definition builder to
# construct a semantic model refresh definition for each semantic model
power_bi_assets = [
    build_semantic_model_refresh_asset_definition(resource_key="power_bi", spec=spec)
    if spec.tags.get("dagster-powerbi/asset_type") == "semantic_model"
    else spec
    for spec in load_powerbi_asset_specs(power_bi_workspace)
]
defs = dg.Definitions(
    assets=[*power_bi_assets], resources={"power_bi": power_bi_workspace}
)
```

You can then add these semantic models to jobs or as targets of Dagster sensors or schedules to trigger refreshes of the models on a cadence or based on other conditions.

### Customizing how Power BI semantic models are materialized

Instead of using the out-of-the-box <PyObject section="libraries" module="dagster_powerbi" object="build_semantic_model_refresh_asset_definition" /> utility, you can build your own asset definitions that trigger the refresh of Power BI semantic models. This allows you to customize how the refresh is triggered or to run custom code before or after the refresh.

{/* TODO convert to <CodeExample> */}
```python file=/integrations/power-bi/materialize-semantic-models-advanced.py
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
```
