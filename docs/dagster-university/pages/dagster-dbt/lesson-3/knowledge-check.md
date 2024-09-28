---
title: 'Knowledge check'
module: 'dagster_essentials'
lesson: '3'
---

# Knowledge check

1. Open the `dbt.py` file.

2. Modify `dbt_analytics` to run `dbt build` instead of `dbt run`. The function should look like this afterward:

   ```python
   @dbt_assets(
       manifest=dbt_project.manifest_path
   )
   def dbt_analytics(context: AssetExecutionContext, dbt: DbtCliResource):
       yield from dbt.cli(["build"], context=context).stream()
   ```

3. In the Dagster UI, re-materialize both of the dbt models.

4. Navigate to the details page for the run you just started, then look at the logs.

When finished, proceed to the next page.