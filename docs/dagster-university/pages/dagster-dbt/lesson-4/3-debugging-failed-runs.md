---
title: 'Lesson 4: Debugging failed runs'
module: 'dagster_dbt'
lesson: '4'
---

# Debugging failed runs

Data engineers spend more time debugging failures than writing new pipelines, so it’s important to know how to debug a failing dbt execution step.

To demonstrate, we’re going to intentionally make a bug in our dbt model code, see it fail in Dagster, troubleshoot the failure, and then re-run the pipeline. Here, you’ll learn how to debug your dbt assets similarly to how you would troubleshoot dbt on its own.

1. Open the `stg_zones.sql` file and add a new column called `zone_population` to the `select` statement. Your code should look like the following:

   ```sql
   with raw_zones as (
       select *
       from {{ source('raw_taxis', 'zones') }}
   )
   select
       zone_id,
       zone as zone_name,
       borough,
       zone_name like '%Airport' as is_airport,
       zone_population ## new column
   from raw_zones
   ```

2. Navigate to the Dagster UI and reload the code location by either clicking the **Reload Definitions** button or using **Option+Shift+R**.

3. On the asset graph, locate the `stg_zones` asset. You’ll see a yellow **Code version** tag indicating that Dagster recognized the SQL code changed:

   ![dbt std_zones asset with a code version badge in the Dagster UI](/images/dagster-dbt/lesson-4/stg-zones-code-version.png)

4. Select the `stg_zones` asset and click the **Materialize** button.

5. Navigate to the run’s details page.

6. On the run’s details page, click the `dbt_analytics` step.

7. To view the logs, click the `stdout` button on the top-left of the pane. You’ll see the logs that typically come from executing `dbt`:

   ![stdout logs showing failure for std_zones materialization in the Dagster UI](/images/dagster-dbt/lesson-4/stg-zones-stdout-failure.png)

In these logs, we can see that DuckDB can’t find the `zone_population` column in `stg_zones`. That’s because this column doesn’t exist!

Now that we know what the problem is, let’s fix it:

1. Remove the `zone_population` column from the `stg_zones` model
2. In the Dagster UI, reload the code location to allow Dagster to pick up the changes.

At this point, if you materialize the  `stg_zones` asset again, the run should be successful:

![Successful materialization of std_zones asset](/images/dagster-dbt/lesson-4/std-zones-success.png)
