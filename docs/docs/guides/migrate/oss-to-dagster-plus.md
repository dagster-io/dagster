---
title: 'Dagster OSS to Dagster+'
sidebar_position: 30
---

## Step 1: Get started with Dagster+

First, you will need to create a Dagster+ organization, choose your deployment type (Hybrid or Serverless), and set up users and authentication. To get started, see the [Dagster+ documentation](/dagster-plus/getting-started).

## Step 2: Update CI/CD pipeline

Next, you will need to modify the CI/CD process that deploys your OSS code to follow the Dagster+ deployment pattern. For more information, see the [Dagster+ CI/CD documentation](/dagster-plus/features/ci-cd/configuring-ci-cd).

## Step 3: Populate metadata in Dagster+

At this point, you should have the same data pipelines in OSS and Dagster+, but the metadata in Dagster+ will be empty. You can either cut over to Dagster+ and start populating metadata after that point, or migrate historical metadata from OSS.

### Option 1: Populate metadata after cutover

If you don't need to migrate historical metadata from your OSS deployment to Dagster+, you can turn off your Dagster OSS deployment and enable the schedules, sensors, and other metadata tracking features in Dagster+. Metadata will start to appear in Dagster+ from that point forward as assets are materialized.

### Option 2: Migrate historical metadata

To migrate historical metadata from your OSS deployment to Dagster+, follow the steps in the [OSS metadata to plus example](https://github.com/dagster-io/dagster/tree/master/examples/oss-metadata-to-plus).
