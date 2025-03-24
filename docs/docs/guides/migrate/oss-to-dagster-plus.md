---
title: 'Dagster OSS to Dagster+'
sidebar_position: 30
---

## Step 1: Get started with Dagster+

- Create a Dagster+ org
- Choose your deployment type (Hybrid or Serverless)
- Set up users and authentication

## Step 2: Update CI/CD pipeline

Then they should take their existing CICD pipeline that deploys their OSS code and modify it to instead follow the Dagster+ deployment pattern (also covered in the getting started docs)

## Step 3: Populate metadata in Dagster+

At this point, you should have the same pipelines in OSS and Dagster+, but the metadata in Dagster+ will be empty. You can either cut over to Dagster+ and start populating metadata after that point, or migrate historical metadata from OSS.

### Option 1: Populate metadata after cutover

If you don't need to migrate historical metadata from your OSS deployment to Dagster+, you can simply turn off your Dagster OSS deployment and enable the schedules, sensors, and other metadata tracking features in Dagster+. Metadata will start to appear in Dagster+ from that point forward as assets are materialized.

### Option 2: Migrate historical metadata

To migrate historical metadata from your OSS deployment to Dagster+, follow the steps in the [OSS metadata to plus example repository](https://github.com/yuhan/oss-metadata-to-plus-example).
