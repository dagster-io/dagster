---
title: Automate your pipeline
description: Set schedules and utilize asset based automation
sidebar_position: 60
---

There are several ways to automate assets [in Dagster](/guides/automate). In this step you will:

- Add automation to assets to run when upstream assets are materialized.

## 1. Scheduled assets

Cron-based schedules are common in data orchestration. For our pipeline, assume that updated CSVs are uploaded to a file location at a specific time every week by an external process.

If we look back at the `joined_data` asset we defined earlier we can now discuss the `automation_condition` within the `dg.asset` decorator. This is [declarative automation](/guides/automate/declarative-automation), which understands the status of an asset and all of its dependencies. We can use declarative automation for a number of different workflows. In this case we can attach a schedule directly to the asset. Now everyday at midnight, the `joined_data` will execute.

This is just one way we can use declarative automation.

## 2. Other asset automation

Now let's look at `monthly_sales_performance`. This asset should be executed once a month, but setting up an independent monthly schedule for this asset isn't exactly what we want -- if we do it naively, then this asset will execute exactly on the month boundary before the last week's data has had a chance to complete. We could delay the monthly schedule by a couple of hours to give the upstream assets a chance to finish, but what if the upstream computation fails or takes too long to complete?

We already set this in the `monthly_sales_performance` and `product_performance` by setting the `automation_condition`. We want it to update when all the dependencies are updated. To accomplish this, we will use the `eager` automation condition.

## Summary

Associating automation directly with assets provides flexibility and allows you to compose complex automation conditions across your data platform.  

## Next steps

- Continue this tutorial with adding a [sensor based asset](/etl-pipeline-tutorial/create-a-sensor)
