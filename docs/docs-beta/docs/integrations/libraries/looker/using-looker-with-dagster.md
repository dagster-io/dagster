---
title: "Using Looker with Dagster"
description: Represent your Looker assets in Dagster
---

:::

This feature is considered **experimental**

:::


This guide provides instructions for using Dagster with Looker using the `dagster-looker` library. Your Looker assets, such as views, explores, and dashboards, can be represented in the Dagster asset graph, allowing you to track lineage and dependencies between Looker assets. You can also use Dagster to orchestrate Looker PDTs, allowing you to trigger refreshes of these materialized tables on a cadence or based on upstream data changes.

## What you'll learn

- How to represent Looker assets in the Dagster asset graph.
- How to customize asset definition metadata for these Looker assets.
- How to materialize Looker PDTs from Dagster.

<details>
  <summary>Prerequisites</summary>

- The `dagster-looker` library installed in your environment
- Familiarity with asset definitions and the Dagster asset graph
- Familiarity with Dagster resources
- Familiarity with Looker concepts, like views, explores, and dashboards
- A Looker instance
- Looker API credentials to access your Looker instance. For more information, see [Looker API authentication](https://cloud.google.com/looker/docs/api-auth) in the Looker documentation.

</details>

## Set up your environment

To get started, you'll need to install the `dagster` and `dagster-looker` Python packages:

```bash
pip install dagster dagster-looker
```

## Represent Looker assets in the asset graph

To load Looker assets into the Dagster asset graph, you must first construct a <PyObject section="libraries" module="dagster_looker" object="LookerResource" />, which allows Dagster to communicate with your Looker instance. You'll need to supply your Looker instance URL and API credentials, which can be passed directly or accessed from the environment using <PyObject section="resources" module="dagster" object="EnvVar" />.

Dagster can automatically load all views, explores, and dashboards from your Looker instance as asset specs. Call the <PyObject section="libraries" module="dagster_looker" object="load_looker_asset_specs" /> function, which returns a list of <PyObject section="assets" module="dagster" object="AssetSpec" pluralize /> representing your Looker assets. You can then include these asset specs in your <PyObject section="definitions" module="dagster" object="Definitions" /> object:

{/* TODO convert to <CodeExample> */}
```python file=/integrations/looker/representing-looker-assets.py
from dagster_looker import LookerResource, load_looker_asset_specs

import dagster as dg

looker_resource = LookerResource(
    client_id=dg.EnvVar("LOOKERSDK_CLIENT_ID"),
    client_secret=dg.EnvVar("LOOKERSDK_CLIENT_SECRET"),
    base_url=dg.EnvVar("LOOKERSDK_HOST_URL"),
)

looker_specs = load_looker_asset_specs(looker_resource=looker_resource)
defs = dg.Definitions(assets=[*looker_specs], resources={"looker": looker_resource})
```

## Load Looker assets from filtered dashboards and explores

It is possible to load a subset of your Looker assets by providing a <PyObject section="libraries" module="dagster_looker" object="LookerFilter" /> to the <PyObject section="libraries" module="dagster_looker" object="load_looker_asset_specs" /> function. All dashboards contained in the folders provided to your <PyObject section="libraries" module="dagster_looker" object="LookerFilter" /> will be fetched. Additionally, only the explores used in these dashboards will be fetched by passing `only_fetch_explores_used_in_dashboards=True` to your <PyObject section="libraries" module="dagster_looker" object="LookerFilter" />.

Note that the content and size of Looker instance may affect the performance of your Dagster deployments. Filtering the dashboards and explores selection from which your Looker assets will be loaded is particularly useful for improving loading times.

{/* TODO convert to <CodeExample> */}
```python file=/integrations/looker/filtering-looker-assets.py
from dagster_looker import LookerFilter, LookerResource, load_looker_asset_specs

import dagster as dg

looker_resource = LookerResource(
    client_id=dg.EnvVar("LOOKERSDK_CLIENT_ID"),
    client_secret=dg.EnvVar("LOOKERSDK_CLIENT_SECRET"),
    base_url=dg.EnvVar("LOOKERSDK_HOST_URL"),
)

looker_specs = load_looker_asset_specs(
    looker_resource=looker_resource,
    looker_filter=LookerFilter(
        dashboard_folders=[
            ["my_folder", "my_subfolder"],
            ["my_folder", "my_other_subfolder"],
        ],
        only_fetch_explores_used_in_dashboards=True,
    ),
)
defs = dg.Definitions(assets=[*looker_specs], resources={"looker": looker_resource})
```

### Customize asset definition metadata for Looker assets

By default, Dagster will generate asset specs for each Looker asset based on its type, and populate default metadata. You can further customize asset properties by passing a custom <PyObject section="libraries" module="dagster_looker" object="DagsterLookerApiTranslator" /> subclass to the <PyObject section="libraries" module="dagster_looker" object="load_looker_asset_specs" /> function. This subclass can implement methods to customize the asset specs for each Looker asset type.

{/* TODO convert to <CodeExample> */}
```python file=/integrations/looker/customize-looker-assets.py
from dagster_looker import (
    DagsterLookerApiTranslator,
    LookerApiTranslatorStructureData,
    LookerResource,
    LookerStructureType,
    load_looker_asset_specs,
)

import dagster as dg

looker_resource = LookerResource(
    client_id=dg.EnvVar("LOOKERSDK_CLIENT_ID"),
    client_secret=dg.EnvVar("LOOKERSDK_CLIENT_SECRET"),
    base_url=dg.EnvVar("LOOKERSDK_HOST_URL"),
)


class CustomDagsterLookerApiTranslator(DagsterLookerApiTranslator):
    def get_asset_spec(
        self, looker_structure: LookerApiTranslatorStructureData
    ) -> dg.AssetSpec:
        # We create the default asset spec using super()
        default_spec = super().get_asset_spec(looker_structure)
        # We customize the team owner tag for all assets,
        # and we customize the asset key prefix only for dashboards.
        return default_spec.replace_attributes(
            key=(
                default_spec.key.with_prefix("looker")
                if looker_structure.structure_type == LookerStructureType.DASHBOARD
                else default_spec.key
            ),
            owners=["team:my_team"],
        )


looker_specs = load_looker_asset_specs(
    looker_resource, dagster_looker_translator=CustomDagsterLookerApiTranslator()
)
defs = dg.Definitions(assets=[*looker_specs], resources={"looker": looker_resource})
```

Note that `super()` is called in each of the overridden methods to generate the default asset spec. It is best practice to generate the default asset spec before customizing it.

### Materialize Looker PDTs from Dagster

You can use Dagster to orchestrate the materialization of Looker PDTs. To model PDTs as assets, build their asset definitions by passing a list of <PyObject section="libraries" module="dagster_looker" object="RequestStartPdtBuild" /> to <PyObject section="libraries" module="dagster_looker" object="build_looker_pdt_assets_definitions" /> function.

{/* TODO convert to <CodeExample> */}
```python file=/integrations/looker/materializing-looker-pdts.py
from dagster_looker import (
    LookerResource,
    RequestStartPdtBuild,
    build_looker_pdt_assets_definitions,
    load_looker_asset_specs,
)

import dagster as dg

looker_resource = LookerResource(
    client_id=dg.EnvVar("LOOKERSDK_CLIENT_ID"),
    client_secret=dg.EnvVar("LOOKERSDK_CLIENT_SECRET"),
    base_url=dg.EnvVar("LOOKERSDK_HOST_URL"),
)

looker_specs = load_looker_asset_specs(looker_resource=looker_resource)

pdts = build_looker_pdt_assets_definitions(
    resource_key="looker",
    request_start_pdt_builds=[
        RequestStartPdtBuild(model_name="my_model", view_name="my_view")
    ],
)


defs = dg.Definitions(
    assets=[*pdts, *looker_specs],
    resources={"looker": looker_resource},
)
```

### Related

- [`dagster-looker` API reference](/api/python-api/libraries/dagster-looker)
- [Asset definitions](/guides/build/assets/defining-assets)
- [Resources](/guides/build/external-resources/)
- [Using environment variables and secrets](/guides/deploy/using-environment-variables-and-secrets)
