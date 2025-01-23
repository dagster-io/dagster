---
title: Machine Learning Pipelines
description: Learn how to build machine learning pipelines
last_update:
   author: Dennis Hume
sidebar_position: 10
---

# Machine Learning Pipelines

In this tutorial, you'll build an ML pipeline with Dagster that:

- Ingests data from Hackernews
- Transform data and train a model
- Use Declarative Automation to manage the life cycle of a model

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.9+ installed on your system. Refer to the [Installation guide](/getting-started/installation) for information.
- Familiarity with Python machine learning libraries.
</details>


## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Create and activate a virtual environment:

   <Tabs>
   <TabItem value="macos" label="MacOS">
   ```bash
   uv venv dagster_tutorial
   source dagster_tutorial/bin/activate
   ```
   </TabItem>
   <TabItem value="windows" label="Windows">
   ```bash
   uv venv dagster_tutorial
   dagster_tutorial\Scripts\activate
   ```
   </TabItem>
   </Tabs>

2. Install Dagster and the required dependencies:

   ```bash
   uv pip install dagster dagster-slack sklearn xgboost numpy
   ```

## Next steps

- Continue this tutorial with [building machine learning pipelines](building-machine-learning-pipelines)