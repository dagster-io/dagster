---
title: 'Lesson 6: Creating a partitioned dbt asset'
module: 'dagster_dbt'
lesson: '6'
---

# Creating a partitioned dbt asset

We’ve built the foundation on the dbt side, and now we can make the appropriate changes on the Dagster side. We’ll refactor our existing Dagster code to tell dbt that the incremental models are partitioned and what data to fill in.

We want to configure some of these models (the incremental ones) with partitions. In this section, we’ll show you a use case that has multiple `@dbt_assets` definitions.

To partition an incremental dbt model, you’ll need first to partition your `@dbt_assets` definition. Then, when it runs, we’ll figure out what partition is running and tell dbt what the partition’s range is. Finally, we’ll modify our dbt model only to insert the records found in that range.

---

## Defining an incremental selector

We have a few changes to make to our dbt setup to get things working. In `assets/dbt.py`:

1. Add the following imports to the top of the file:

   ```python
   from ..partitions import daily_partition
   import json
   ```

   This imports the `daily_partition` from `dagster_university/partitions/__init__.py` and the `json` standard module. We’ll use the `json` module to format how we tell dbt what partition to materialize.

2. We now need a way to indicate that we’re selecting or excluding incremental models, so we’ll make a new constant in the `dbt.py` file called `INCREMENTAL_SELECTOR:`

   ```python
   INCREMENTAL_SELECTOR = "config.materialized:incremental"
   ```

   This string follows dbt’s selection syntax to select all incremental models. In your own projects, you can customize this to select only the specific incremental models that you want to partition.

---

## Creating a new @dbt_assets function

Previously, we used the `@dbt_assets` decorator to say _“this function produces assets based on this dbt project”_. Now, we also want to say _“this function produces partitioned assets based on a selected set of models from this dbt project.”_ We’ll write an additional `@dbt_assets` -decorated function to express this.

1. In `dagster_university/assets/dbt.py`, define another `@dbt_assets` function below the original one. Name it `dbt_incremental_models` and have it use the same manifest that we’ve been using:

   ```python
   @dbt_assets(
       manifest=dbt_project.manifest_path,
       dagster_dbt_translator=CustomizedDagsterDbtTranslator()
   )
   def incremental_dbt_models(
       context: AssetExecutionContext,
       dbt: DbtCliResource
   ):
       yield from dbt.cli(["build"], context=context).stream()
   ```

2. Next, add arguments to specify which models to select (`select`) and what partition (`partitions_def`) to use:

   ```python
   @dbt_assets(
       manifest=dbt_project.manifest_path,
       dagster_dbt_translator=CustomizedDagsterDbtTranslator(),
       select=INCREMENTAL_SELECTOR,     # select only models with INCREMENTAL_SELECTOR
       partitions_def=daily_partition   # partition those models using daily_partition
   )
   def incremental_dbt_models(
       context: AssetExecutionContext,
       dbt: DbtCliResource
   ):
     yield from dbt.cli(["build"], context=context).stream()
   ```

   This tells the function to only select models with `INCREMENTAL_SELECTOR` and to partition them using the `daily_partition.`

---

## Partitioning the incremental_dbt_models function

Now that the `@dbt_assets` definition has been created, it's time to fill in its body. We’ll start by using the `context` argument, which contains metadata about the Dagster run.

One of these pieces of information is that we can fetch _the partition this execution is trying to materialize_! In our case, since it’s a time-based partition, we can get the _time window_ of the partitions we’re materializing, such as `2023-03-04T00:00:00+00:00`to `2023-03-05T00:00:00+00:00`.

First, add the following to the `@dbt_assets` function body, before the `yield`:

```bash
time_window = context.partition_time_window
dbt_vars = {
    "min_date": time_window.start.strftime('%Y-%m-%d'),
    "max_date": time_window.end.strftime('%Y-%m-%d')
}
```

This fetches the time window and stores it as a variable (`time_window` ) so we can use it later.

Now that we know _what_ partitions we’re executing, the next step is to tell dbt the partition currently being materialized. To do that, we’ll take advantage of dbt’s `vars` argument to pass this information at runtime.
Because the `dbt.cli` function has the same capabilities as the `dbt` CLI, we can dynamically set the arguments we pass into it. To communicate this time window, we’ll pass in a `min_date` and `max_date` variable. Update the `yield` in the `@dbt_assets` definition to the following:

```python
yield from dbt.cli(["build", "--vars", json.dumps(dbt_vars)], context=context).stream()
```

---

## Updating the dbt_analytics function

Now that you have a dedicated `@dbt_assets` definition for the incremental models, you’ll need to _exclude_ these models from your original dbt execution.

Modify the `dbt_analytics` definition to exclude the `INCREMENTAL_SELECTOR`:

```python
@dbt_assets(
    manifest=dbt_project.manifest_path,
    dagster_dbt_translator=CustomizedDagsterDbtTranslator(),
    exclude=INCREMENTAL_SELECTOR, # Add this here
)
def dbt_analytics(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()
```

At this point, the `dagster_university/assets/dbt.py` file should look like this:

```python
import json

from dagster import AssetExecutionContext, AssetKey
from dagster_dbt import DagsterDbtTranslator, DbtCliResource, dbt_assets

from ..partitions import daily_partition
from ..project import dbt_project

INCREMENTAL_SELECTOR = "config.materialized:incremental"


class CustomizedDagsterDbtTranslator(DagsterDbtTranslator):
    def get_asset_key(self, dbt_resource_props):
        resource_type = dbt_resource_props["resource_type"]
        name = dbt_resource_props["name"]
        if resource_type == "source":
            return AssetKey(f"taxi_{name}")
        else:
            return super().get_asset_key(dbt_resource_props)


@dbt_assets(
    manifest=dbt_project.manifest_path,
    dagster_dbt_translator=CustomizedDagsterDbtTranslator(),
    exclude=INCREMENTAL_SELECTOR,
)
def dbt_analytics(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


@dbt_assets(
    manifest=dbt_project.manifest_path,
    dagster_dbt_translator=CustomizedDagsterDbtTranslator(),
    select=INCREMENTAL_SELECTOR,
    partitions_def=daily_partition,
)
def incremental_dbt_models(context: AssetExecutionContext, dbt: DbtCliResource):
    time_window = context.partition_time_window
    dbt_vars = {
        "min_date": time_window.start.strftime('%Y-%m-%d'),
        "max_date": time_window.end.strftime('%Y-%m-%d')
    }

    yield from dbt.cli(
        ["build", "--vars", json.dumps(dbt_vars)], context=context
    ).stream()

```

---

## Updating the daily_metrics model

Finally, we’ll modify the `daily_metrics.sql` file to reflect that dbt knows what partition range is being materialized. Since the partition range is passed in as variables at runtime, the dbt model can access them using the `var` dbt macro.

In `analytics/models/marts/daily_metrics.sql`, update the contents of the model's incremental logic (`% if is_incremental %}`) to the following:

```sql
where date_of_business between '{{ var('min_date') }}' and '{{ var('max_date') }}'
```

Here, we’ve changed the logic to say that we only want to select rows between the `min_date` and the `max_date`.

---

## Running the pipeline

That’s it! Now you can check out the new `daily_metrics` asset in Dagster.

1. In the Dagster UI, reload the code location. Once loaded, you should see the new partitioned `daily_metrics` asset:

   ![daily_metrics asset in the Asset Graph of the Dagster UI](/images/dagster-dbt/lesson-6/daily-metrics-asset.png)

2. Click the `daily_metrics` asset and then the **Materialize selected** button. You’ll be prompted to select some partitions first.
3. Once the run starts, navigate to the run’s details page to check out the event logs. The executed dbt command should look something like this:
   ```bash
   dbt build --vars {"min_date": "2023-03-04T00:00:00+00:00", "max_date": "2023-03-05T00:00:00+00:00"} --select config.materialized:incremental
   ```
