---
title: IBM DataStage with Dagster
description: Learn how to orchestrate IBM DataStage jobs with Dagster using a custom component, multi-asset pattern, and inline data quality checks
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/integrations/ibm.png
tags: [code-example]
canonicalUrl: '/examples/full-pipelines/datastage'
slug: '/examples/full-pipelines/datastage'
---

In this example, you'll build a pipeline with Dagster that:

- Wraps [IBM DataStage](https://www.ibm.com/products/datastage) replication jobs as Dagster [multi-assets](/guides/build/assets/defining-assets#multi-asset)
- Runs inline data quality checks in the same step as materialization
- Uses a translator pattern to map DataStage tables to Dagster asset keys
- Configures everything with a YAML-based Dagster component

## Prerequisites

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.10+ installed on your system. For more information, see the [Installation guide](/getting-started/installation).
- Familiarity with IBM DataStage

:::note
This example runs in demo mode and doesn't require the [`cpdctl`](https://github.com/IBM/cpdctl/) CLI. If you want to run this example against a real DataStage instance, follow the [IBM installation instructions](https://github.com/IBM/cpdctl/?tab=readme-ov-file#installation) and set `demo_mode: false` in the YAML configuration.
:::

## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Clone the [Dagster repo](https://github.com/dagster-io/dagster) and navigate to the project:

   ```bash
   cd examples/docs_projects/project_datastage
   ```

2. Install the required dependencies with `uv`:

   ```bash
   uv sync
   ```

3. Activate the virtual environment:

   <Tabs>
     <TabItem value="macos" label="MacOS">
       ```source .venv/bin/activate ```
     </TabItem>
     <TabItem value="windows" label="Windows">
       ```.venv\Scripts\activate ```
     </TabItem>
   </Tabs>

## Step 2: Launch the Dagster webserver

Navigate to the project root directory and start the Dagster webserver:

```bash
dg dev
```

:::note
With `demo_mode: true` set in the YAML configuration, the project simulates a DataStage replication job locally without a `cpdctl` installation.
:::

## Next steps

- Continue this example with [defining assets](/examples/full-pipelines/datastage/defining-assets)
