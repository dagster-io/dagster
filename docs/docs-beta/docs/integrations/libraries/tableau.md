---
layout: Integration
status: published
name: Tableau
title: Dagster & Tableau
sidebar_label: Tableau
excerpt: See and understand your data with Tableau through Dagster.
date: 
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-tableau
docslink:
partnerlink:
categories:
  - Other
enabledBy:
enables:
tags: [dagster-supported, bi]
sidebar_custom_props:
  logo: images/integrations/tableau.svg
---

:::note

This integration is currently **experimental**.

:::

This guide provides instructions for using Dagster with Tableau using the `dagster-tableau` library. Your Tableau assets, such as data sources, sheets, and dashboards, can be represented in the Dagster asset graph, allowing you to track lineage and dependencies between Tableau assets and upstream data assets you are already modeling in Dagster.


## What you'll learn

- How to represent Tableau assets in the Dagster asset graph.

- How to customize asset definition metadata for these Tableau assets.

- How to refresh Tableau workbooks.

- How to materialize Tableau sheets and dashboards.

<details>
  <summary>Prerequisites</summary>

- The `dagster-tableau` library installed in your environment
- Familiarity with asset definitions and the Dagster asset graph
- Familiarity with Dagster resources
- Familiarity with Tableau concepts, like data sources, sheets, and dashboards
- A Tableau site, either on Tableau Cloud or Tableau Server
- A connected app configured to access Tableau. For more information, see [Use Tableau Connected Apps for Application Integration](https://help.tableau.com/current/online/en-us/connected_apps.htm) in the Tableau documentation.

</details>

## Set up your environment

To get started, you'll need to install the `dagster` and `dagster-tableau` Python packages:

```bash
pip install dagster dagster-tableau
```

## Represent Tableau assets in the asset graph

To load Tableau assets into the Dagster asset graph, you must first construct a Tableau resource, which allows Dagster to communicate with your Tableau workspace. The Tableau resource to create depends on your Tableau deployment type - use <PyObject section="libraries" module="dagster_tableau" object="TableauCloudWorkspace" /> if you are using Tableau Cloud or <PyObject section="libraries" module="dagster_tableau" object="TableauServerWorkspace" /> if you are using Tableau Server. To connect to the Tableau workspace, you'll need to [configure a connected app with direct trust](https://help.tableau.com/current/online/en-gb/connected_apps_direct.htm) in Tableau, then supply your Tableau site information and connected app credentials to the resource. The Tableau resource uses the JSON Web Token (JWT) authentication to connect to the Tableau workspace.

Dagster can automatically load all data sources, sheets, and dashboards from your Tableau workspace as asset specs. Call the <PyObject section="libraries" module="dagster_tableau" object="load_tableau_asset_specs" /> function, which returns a list of <PyObject section="assets" module="dagster" object="AssetSpec" pluralize /> representing your Tableau assets. You can then include these asset specs in your <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<Tabs>
<TabItem value="Using Dagster with Tableau Cloud">

Use <PyObject section="libraries" module="dagster_tableau" object="TableauCloudWorkspace" /> to interact with your Tableau Cloud workspace:

{/* TODO convert to <CodeExample> */}
```python file=/integrations/tableau/representing-tableau-cloud-assets.py
from dagster_tableau import TableauCloudWorkspace, load_tableau_asset_specs

import dagster as dg

# Connect to Tableau Cloud using the connected app credentials
tableau_workspace = TableauCloudWorkspace(
    connected_app_client_id=dg.EnvVar("TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=dg.EnvVar("TABLEAU_USERNAME"),
    site_name=dg.EnvVar("TABLEAU_SITE_NAME"),
    pod_name=dg.EnvVar("TABLEAU_POD_NAME"),
)

tableau_specs = load_tableau_asset_specs(tableau_workspace)
defs = dg.Definitions(assets=[*tableau_specs], resources={"tableau": tableau_workspace})
```

</TabItem>
<TabItem value="Using Dagster with Tableau Server">

Use <PyObject section="libraries" module="dagster_tableau" object="TableauServerWorkspace" /> to interact with your Tableau Server workspace:

{/* TODO convert to <CodeExample> */}
```python file=/integrations/tableau/representing-tableau-server-assets.py
from dagster_tableau import TableauServerWorkspace, load_tableau_asset_specs

import dagster as dg

# Connect to Tableau Server using the connected app credentials
tableau_workspace = TableauServerWorkspace(
    connected_app_client_id=dg.EnvVar("TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=dg.EnvVar("TABLEAU_USERNAME"),
    site_name=dg.EnvVar("TABLEAU_SITE_NAME"),
    server_name=dg.EnvVar("TABLEAU_SERVER_NAME"),
)

tableau_specs = load_tableau_asset_specs(tableau_workspace)
defs = dg.Definitions(assets=[*tableau_specs], resources={"tableau": tableau_workspace})
```

</TabItem>
</Tabs>

### Customize asset definition metadata for Tableau assets

By default, Dagster will generate asset specs for each Tableau asset based on its type, and populate default metadata. You can further customize asset properties by passing a custom <PyObject section="libraries" module="dagster_tableau" object="DagsterTableauTranslator" /> subclass to the <PyObject section="libraries" module="dagster_tableau" object="load_tableau_asset_specs" /> function. This subclass can implement methods to customize the asset specs for each Tableau asset type.

{/* TODO convert to <CodeExample> */}
```python file=/integrations/tableau/customize-tableau-asset-defs.py
from dagster_tableau import (
    DagsterTableauTranslator,
    TableauCloudWorkspace,
    load_tableau_asset_specs,
)
from dagster_tableau.translator import TableauContentType, TableauTranslatorData

import dagster as dg

tableau_workspace = TableauCloudWorkspace(
    connected_app_client_id=dg.EnvVar("TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=dg.EnvVar("TABLEAU_USERNAME"),
    site_name=dg.EnvVar("TABLEAU_SITE_NAME"),
    pod_name=dg.EnvVar("TABLEAU_POD_NAME"),
)


# A translator class lets us customize properties of the built
# Tableau assets, such as the owners or asset key
class MyCustomTableauTranslator(DagsterTableauTranslator):
    def get_asset_spec(self, data: TableauTranslatorData) -> dg.AssetSpec:
        # We create the default asset spec using super()
        default_spec = super().get_asset_spec(data)
        # We customize the metadata and asset key prefix for all assets, including sheets,
        # and we customize the team owner tag only for sheets.
        return default_spec.replace_attributes(
            key=default_spec.key.with_prefix("prefix"),
            metadata={**default_spec.metadata, "custom": "metadata"},
            owners=(
                ["team:my_team"]
                if data.content_type == TableauContentType.SHEET
                else ...
            ),
        )


tableau_specs = load_tableau_asset_specs(
    tableau_workspace,
    dagster_tableau_translator=MyCustomTableauTranslator(),
)
defs = dg.Definitions(assets=[*tableau_specs], resources={"tableau": tableau_workspace})
```

Note that `super()` is called in each of the overridden methods to generate the default asset spec. It is best practice to generate the default asset spec before customizing it.

### Load Tableau assets from multiple workspaces

Definitions from multiple Tableau workspaces can be combined by instantiating multiple Tableau resources and merging their specs. This lets you view all your Tableau assets in a single asset graph:

{/* TODO convert to <CodeExample> */}
```python file=/integrations/tableau/multiple-tableau-workspaces.py
from dagster_tableau import TableauCloudWorkspace, load_tableau_asset_specs

import dagster as dg

sales_team_workspace = TableauCloudWorkspace(
    connected_app_client_id=dg.EnvVar("SALES_TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=dg.EnvVar("SALES_TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=dg.EnvVar("SALES_TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=dg.EnvVar("TABLEAU_USERNAME"),
    site_name=dg.EnvVar("SALES_TABLEAU_SITE_NAME"),
    pod_name=dg.EnvVar("SALES_TABLEAU_POD_NAME"),
)

marketing_team_workspace = TableauCloudWorkspace(
    connected_app_client_id=dg.EnvVar("MARKETING_TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=dg.EnvVar("MARKETING_TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=dg.EnvVar(
        "MARKETING_TABLEAU_CONNECTED_APP_SECRET_VALUE"
    ),
    username=dg.EnvVar("TABLEAU_USERNAME"),
    site_name=dg.EnvVar("MARKETING_TABLEAU_SITE_NAME"),
    pod_name=dg.EnvVar("MARKETING_TABLEAU_POD_NAME"),
)


sales_team_specs = load_tableau_asset_specs(sales_team_workspace)
marketing_team_specs = load_tableau_asset_specs(marketing_team_workspace)

defs = dg.Definitions(
    assets=[*sales_team_specs, *marketing_team_specs],
    resources={
        "marketing_tableau": marketing_team_workspace,
        "sales_tableau": sales_team_workspace,
    },
)
```

### Refresh and materialize Tableau assets

You can use Dagster to refresh Tableau workbooks and materialize Tableau sheets and dashboards.

{/* TODO convert to <CodeExample> */}
```python file=/integrations/tableau/refresh-and-materialize-tableau-assets.py
from dagster_tableau import (
    TableauCloudWorkspace,
    build_tableau_materializable_assets_definition,
    load_tableau_asset_specs,
    parse_tableau_external_and_materializable_asset_specs,
)

import dagster as dg

tableau_workspace = TableauCloudWorkspace(
    connected_app_client_id=dg.EnvVar("TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=dg.EnvVar("TABLEAU_USERNAME"),
    site_name=dg.EnvVar("TABLEAU_SITE_NAME"),
    pod_name=dg.EnvVar("TABLEAU_POD_NAME"),
)

# Load Tableau asset specs
tableau_specs = load_tableau_asset_specs(
    workspace=tableau_workspace,
)

external_asset_specs, materializable_asset_specs = (
    parse_tableau_external_and_materializable_asset_specs(tableau_specs)
)

# Use the asset definition builder to construct the definition for tableau materializable assets
defs = dg.Definitions(
    assets=[
        build_tableau_materializable_assets_definition(
            resource_key="tableau",
            specs=materializable_asset_specs,
            refreshable_workbook_ids=["b75fc023-a7ca-4115-857b-4342028640d0"],
        ),
        *external_asset_specs,
    ],
    resources={"tableau": tableau_workspace},
)
```

Note that only workbooks created with extracts can be refreshed using this method. See more about [refreshing data sources](https://help.tableau.com/current/pro/desktop/en-us/refreshing_data.htm) in Tableau documentation website.

### Add a Data Quality Warning in Tableau using a sensor

When an upstream dependency of a Tableau asset fails to materialize or to pass the asset checks, it is possible to add a [Data Quality Warning](https://help.tableau.com/current/online/en-us/dm_dqw.htm) to the corresponding data source in Tableau. This can be achieved by leveraging the `add_data_quality_warning_to_data_source` in a sensor.

{/* TODO convert to <CodeExample> */}
```python file=/integrations/tableau/add-tableau-data-quality-warning.py
from dagster_tableau import (
    TableauCloudWorkspace,
    build_tableau_materializable_assets_definition,
    load_tableau_asset_specs,
    parse_tableau_external_and_materializable_asset_specs,
)

import dagster as dg

# Connect to Tableau Cloud using the connected app credentials
tableau_workspace = TableauCloudWorkspace(
    connected_app_client_id=dg.EnvVar("TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=dg.EnvVar("TABLEAU_USERNAME"),
    site_name=dg.EnvVar("TABLEAU_SITE_NAME"),
    pod_name=dg.EnvVar("TABLEAU_POD_NAME"),
)


@dg.asset(
    # Define which Tableau data source this upstream asset corresponds to
    metadata={"dagster/tableau_data_source_id": "f5660c7-2b05-4ff0-90ce-3199226956c6"}
)
def upstream_asset(): ...


@dg.run_failure_sensor
def tableau_run_failure_sensor(
    context: dg.RunFailureSensorContext, tableau: TableauCloudWorkspace
):
    asset_keys = context.dagster_run.asset_selection or set()
    for asset_key in asset_keys:
        data_source_id = upstream_asset.metadata_by_key.get(asset_key, {}).get(
            "dagster/tableau_data_source_id"
        )
        if data_source_id:
            with tableau.get_client() as client:
                client.add_data_quality_warning_to_data_source(
                    data_source_id=data_source_id, message=context.failure_event.message
                )


tableau_specs = load_tableau_asset_specs(
    workspace=tableau_workspace,
)

external_asset_specs, materializable_asset_specs = (
    parse_tableau_external_and_materializable_asset_specs(tableau_specs)
)

# Pass the sensor, Tableau resource, upstream asset, Tableau assets specs and materializable assets definition at once
defs = dg.Definitions(
    assets=[
        upstream_asset,
        build_tableau_materializable_assets_definition(
            resource_key="tableau",
            specs=materializable_asset_specs,
            refreshable_workbook_ids=["b75fc023-a7ca-4115-857b-4342028640d0"],
        ),
        *external_asset_specs,
    ],
    sensors=[tableau_run_failure_sensor],
    resources={"tableau": tableau_workspace},
)
```

### Customizing how Tableau assets are materialized

Instead of using the out-of-the-box <PyObject section="libraries" module="dagster_tableau" object="build_tableau_materializable_assets_definition" /> utility, you can build your own assets definition that trigger the refresh of your Tableau workbooks. This allows you to customize how the refresh is triggered or to run custom code before or after the refresh.

{/* TODO convert to <CodeExample> */}
```python file=/integrations/tableau/materialize-tableau-assets-advanced.py
from collections.abc import Sequence

from dagster_tableau import (
    TableauCloudWorkspace,
    load_tableau_asset_specs,
    parse_tableau_external_and_materializable_asset_specs,
)

import dagster as dg

tableau_workspace = TableauCloudWorkspace(
    connected_app_client_id=dg.EnvVar("TABLEAU_CONNECTED_APP_CLIENT_ID"),
    connected_app_secret_id=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_ID"),
    connected_app_secret_value=dg.EnvVar("TABLEAU_CONNECTED_APP_SECRET_VALUE"),
    username=dg.EnvVar("TABLEAU_USERNAME"),
    site_name=dg.EnvVar("TABLEAU_SITE_NAME"),
    pod_name=dg.EnvVar("TABLEAU_POD_NAME"),
)


# Assets definition factory which triggers workbooks refresh and sends a notification once complete
def build_tableau_materialize_and_notify_asset_def(
    specs: Sequence[dg.AssetSpec], refreshable_workbook_ids: Sequence[str]
) -> dg.AssetsDefinition:
    @dg.multi_asset(
        name="tableau_sync",
        compute_kind="tableau",
        specs=specs,
    )
    def asset_fn(context: dg.AssetExecutionContext, tableau: TableauCloudWorkspace):
        with tableau.get_client() as client:
            yield from client.refresh_and_materialize_workbooks(
                specs=specs, refreshable_workbook_ids=refreshable_workbook_ids
            )
            # Do some custom work after refreshing here, such as sending an email notification

    return asset_fn


# Load Tableau asset specs
tableau_specs = load_tableau_asset_specs(
    workspace=tableau_workspace,
)

external_asset_specs, materializable_asset_specs = (
    parse_tableau_external_and_materializable_asset_specs(tableau_specs)
)

# Use the asset definition builder to construct the definition for tableau materializable assets
defs = dg.Definitions(
    assets=[
        build_tableau_materialize_and_notify_asset_def(
            specs=materializable_asset_specs,
            refreshable_workbook_ids=["b75fc023-a7ca-4115-857b-4342028640d0"],
        ),
        *external_asset_specs,
    ],
    resources={"tableau": tableau_workspace},
)
```

### Related

- [`dagster-tableau` API reference](/api/python-api/libraries/dagster-tableau)
- [Asset definitions](/guides/build/assets/)
- [Resources](/guides/build/external-resources/)
- [Using environment variables and secrets](/guides/deploy/using-environment-variables-and-secrets)
