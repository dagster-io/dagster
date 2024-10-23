---
title: 'Lesson 5: Automating dbt models in Dagster'
module: 'dagster_dbt'
lesson: '5'
---

# Automating dbt models in Dagster

Did you realize that your dbt models have already been scheduled to run on a regular basis because of an existing schedule within this Dagster project?

Check it out in the Dagster UI by clicking **Overview** in the top navigation bar, then the **Jobs** tab. Click `trip_update_job` to check out the job’s details. It looks like the dbt models are already attached to this job!

![dbt assets in the trip_update_job in the Dagster UI](/images/dagster-dbt/lesson-5/trip-update-job-dbt-assets.png)

Pretty cool, right? Let’s check out the code that made this happen. Open the `dagster_university/jobs/__init__.py` and look at the definition for `trip_update_job`:

```python
trip_update_job = define_asset_job(
    name="trip_update_job",
    partitions_def=monthly_partition,
    selection=AssetSelection.all() - trips_by_week - adhoc_request
)
```

The dbt models were included in this job because of the `AssetSelection.all()` call. This reinforces the idea that once you load your dbt project into your Dagster project, Dagster will recognize and treat all of your dbt models as assets.

---

## Excluding specific dbt models

Treating dbt models as assets is great, but one of the core tenets of Dagster’s dbt integration is respecting how dbt is used, along with meeting dbt users where they are. That’s why there are a few utility methods that should feel familiar to dbt users. Let’s use one of these methods to remove some of our dbt models from this job explicitly.

Pretend that you’re working with an analytics engineer, iterating on the `stg_trips` model and planning to add new models that depend on it soon. Therefore, you’d like to exclude `stg_trips` and any new hypothetical dbt models downstream of it until the pipeline stabilizes. The analytics engineer you’re working with is really strong with dbt, but not too familiar with Dagster.

This is where you’d lean on a function like [`build_dbt_asset_selection`](https://docs.dagster.io/_apidocs/libraries/dagster-dbt#dagster_dbt.build_dbt_asset_selection). This utility method will help your analytics engineer contribute without needing to know Dagster’s asset selection syntax. It takes two arguments:

- A list of `@dbt_assets` definitions to select models from
- A string of the selector using [dbt’s selection syntax](https://docs.getdbt.com/reference/node-selection/syntax) of the models you want to select

The function will return an `AssetSelection` of the dbt models that match your dbt selector. Let’s put this into practice:

1. At the top of `jobs/__init__.py`, import `dbt_analytics` from the `assets.dbt` module, along with the `build_dbt_asset_selection` function from `dagster_dbt`:
    
    ```python
    from ..assets.dbt import dbt_analytics
    from dagster_dbt import build_dbt_asset_selection
    ```
    
2. After the other selections, define a new variable called `dbt_trips_selection` and make a call to `build_dbt_asset_selection`. Pass in the `dbt_analytics` definition and a string that selects `stg_trips` and all dbt models downstream of it:
    
    ```python
    dbt_trips_selection = build_dbt_asset_selection([dbt_analytics], "stg_trips+")
    ```
    
3. Next, update the `selection` argument in the `trip_update_job` to subtract the `dbt_trips_selection`: 
    
    ```python
    trip_update_job = define_asset_job(
        name="trip_update_job",
        partitions_def=monthly_partition,
        selection=AssetSelection.all() - trips_by_week - adhoc_request - dbt_trips_selection
    )
    ```
    
4. Reload the code location and confirm that the dbt models are not in the `trip_update_job` anymore!

   ![trip_update_job without dbt models](/images/dagster-dbt/lesson-5/job-with-dbt-models.png)

You might notice that the `airport_trips` asset is still scheduled to run with this job! That’s because the `build_dbt_asset_selection` function only selects *dbt models* and **not** Dagster assets.

If you want to also exclude the new `airport_trips` asset from this job, modify the `dbt_trips_selection` to include all *downstream assets*, too. Because we’re using Dagster’s native functionality to select all downstream assets, we can now drop the `+` from the dbt selector:

```python
dbt_trips_selection = build_dbt_asset_selection([dbt_analytics], "stg_trips").downstream()
```

Reload the code location and look at the `trip_update_job` once more to verify that everything looks right:

![trip_update_job with the airport_trips asset](/images/dagster-dbt/lesson-5/job-without-dbt-models.png)

{% callout %}
> 💡 **Want an even more convenient utility to do this work for you?** Consider using the similar [`build_schedule_from_dbt_selection`](https://docs.dagster.io/_apidocs/libraries/dagster-dbt#dagster_dbt.build_schedule_from_dbt_selection) function to quickly create a job and schedule for a given dbt selection.
{% /callout %}