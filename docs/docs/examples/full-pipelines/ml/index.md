---
title: Machine learning with PyTorch
description: Build production-ready ML pipelines for handwritten digit classification
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/integrations/pytorch.png
tags: [code-example]
canonicalUrl: '/examples/ml'
slug: '/examples/ml'
---

In this example, you'll build a complete CNN-based digit classifier that:

- Build production-ready ML pipelines using Dagster's asset-based architecture
- Train and deploy CNN models with automated quality gates and rollback capabilities
- Implement configurable training workflows that adapt across development and production environments
- Create scalable inference services supporting both batch and real-time prediction scenarios

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.9+ installed on your system. Refer to the [Installation guide](/getting-started/installation) for information.
- Basic familiarity with machine learning concepts (neural networks, training/validation splits)
- Understanding of PyTorch fundamentals (tensors, models, training loops)

</details>

## Step 1: Set up your Dagster environment

First, set up a new Dagster project with the ML dependencies.

1. Clone the [Dagster repo](https://github.com/dagster-io/dagster) and navigate to the project:

   ```bash
   cd examples/docs_projects/project_ml
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

To make sure Dagster and its dependencies were installed correctly, navigate to the project root directory and start the Dagster webserver:

```bash
dg dev
```

## Next steps

- Continue this example with [data ingestion](/examples/full-pipelines/ml/data-ingestion)
