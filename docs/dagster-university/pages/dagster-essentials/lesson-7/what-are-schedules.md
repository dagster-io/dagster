---
title: 'Lesson 7: What are schedules?'
module: 'dagster_essentials'
lesson: '7'
---

# What are schedules?

Schedules are the most traditional way to keep your assets up-to-date. Schedules define a fixed time interval to run your pipeline, such as daily, hourly, or Monday at 9:00 AM.

Returning to our cookie example, let’s say things at your bakery have really started to take off! To meet demand, all of your cookies must be freshly made before your customers pick them up every morning. Like most bakeries, this happens early in the morning, so you want to start baking at 4:00 AM every day.

For example, the following image highlights the cookie assets that will be materialized, starting every day at 4:00 AM. This means that every day at 4:00 AM, a **tick** would be created, indicating that baking should begin. Ticks kick off a **run,** which is a single instance of baking or asset materialization.

![Cookie pipeline with a 4:00 AM schedule, running every day](/images/dagster-essentials/lesson-7/cookie-schedule.png)

In Dagster, you can define a schedule to express how often a pipeline should run. Dagster will use this schedule and run the pipeline by materializing the assets you specify.

---

## Anatomy of a schedule

Refreshing a series of assets with a schedule has multiple components. The two components that we’ll focus on in this lesson are:

- A job
- A cron expression

Next, we’ll go through each part of the schedule and begin materializing most of the assets on a regular frequency. In particular, you’ll write a schedule that updates your assets every month. This is because the NYC Taxi & Limo Commission (TLC) releases trip data in batches of months.

### Jobs

When working with large asset graphs, you likely don’t want to materialize all of your assets with every run.

Jobs are a Dagster utility to take a slice of your asset graph and focus specifically on running materializations of those assets. As you learn more about Dagster, you’ll also learn more about how to customize your materializations and runs with jobs. For example, having multiple jobs can enable running one set of assets in an isolated Kubernetes pod and another selection of assets on a single process.

As you might have noticed while defining assets and resources, Dagster’s best practice is to store definitions in their own directory/Python sub-module. In the case of jobs, we recommend that you define your jobs within the `jobs/__init__.py` file.

To select only the assets you want to include, you’ll use the `AssetSelection` class. This class lets you look up and reference assets across your code location. In particular, there will be two methods that you’ll be using:

- `AssetSelection.all()` gives you a list of all asset definitions in the code location
- `AssetSelection.assets([<string>, ...])` which gives you a list of assets that match the asset keys provided

For more info on asset selection, refer to the [asset selection syntax guide in the Dagster docs](https://docs.dagster.io/concepts/assets/asset-selection-syntax).

1. In `jobs/__init__.py`, let’s first define our asset selection. Copy and paste the following snippet into the file:

   ```python
   from dagster import AssetSelection

   trips_by_week = AssetSelection.assets("trips_by_week")
   ```

   This uses the `AssetSelection` utility to reference a single asset, `trips_by_week`. We’ll isolate this specifically because we won’t want to run it with the rest of our pipeline and it should be run more frequently.

2. Add `define_asset_job` to your `dagster` import:

   ```bash
   from dagster import AssetSelection, define_asset_job
   ```

3. Next, create a job named `trip_update_job` that selects all assets using `AssetSelection.all()` and then omit `trips_by_week` by substracting its selection:

   ```python
   trip_update_job = define_asset_job(
       name="trip_update_job",
       selection=AssetSelection.all() - trips_by_week
   )
   ```

4. Save your changes and continue.

Your final code in `jobs/__init__.py` should look like the following:

```python
from dagster import AssetSelection, define_asset_job

trips_by_week = AssetSelection.assets("trips_by_week")

trip_update_job = define_asset_job(
    name="trip_update_job",
    selection=AssetSelection.all() - trips_by_week
)
```

### Cron expressions

Cron syntax is the gold standard for how schedules and time intervals are defined. Cron started off as the original scheduling utility in computer programming somewhere around the 1970s.

Despite many schedulers and orchestrators replacing the cron program since then, its syntax for expressing schedules and intervals is still used today. You can use this syntax in Dagster to define schedules that materialize assets:

![Image credit: Crontogo.com](/images/dagster-essentials/lesson-7/crontogo-cron-syntax.png)

Consider the following example:

```
15 5 * * 1-5
```

This expression translates to `Every Monday through Friday of every month at 5:15AM`.

To make creating cron schedules easier, you can use an online tool like [Crontab Guru](https://crontab.guru/). This tool allows you to create and describe cron expressions in a human-readable format and test the execution dates produced by the expression.

**Note**: While this tool is useful for general cron expression testing, always remember to test your schedules in Dagster to ensure the results are as expected.
