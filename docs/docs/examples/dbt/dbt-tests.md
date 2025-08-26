---
title: dbt tests
description: Executing dbt tests through Dagster
last_update:
  author: Dennis Hume
sidebar_position: 50
---

As you may have noticed, while configuring our dbt assets, we didn’t explicitly define anything related to tests. And yet, our dbt project includes tests—specifically, for the `stg_zones` model.

<CodeExample
  path="docs_projects/project_dbt/src/project_dbt/analytics/models/staging/staging.yml"
  language="yaml"
  title="src/project_dbt/analytics/models/staging/staging.yml"
/>

Fortunately, no additional configuration is required to include these tests in Dagster. When Dagster parses the dbt project, it automatically:

- Identifies any associated dbt tests declared in the project.
- Converts them into asset checks, which are then linked to the Dagster asset that represents the model.

For example, the `stg_zones` model has two tests defined in its .yml file. Dagster registers these as two separate asset checks on the `stg_zones` asset.

![2048 resolution](/images/examples/dbt/asset_check.png)

You can see the two asset checks for the model, for the two tests set in the yaml. When the asset executes, its underlying dbt tests will be executed as well and recorded.

![2048 resolution](/images/examples/dbt/asset_check_executed.png)

Once your dbt project is integrated this way, you can view a model’s complete lineage in the Asset Catalog within Dagster:

- The asset’s materialization history (i.e., successful or failed runs).
- A complete history of its associated tests, showing which checks passed or failed over time.

This gives you a unified view of both data freshness and quality, helping you catch regressions or upstream data issues as early as possible.

![2048 resolution](/images/examples/dbt/asset_check_page.png)

## Next steps

- Continue this example with [managing the project](/examples/dbt/managing-the-project)
