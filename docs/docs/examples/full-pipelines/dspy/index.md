---
title: Solving NYT Connections with DSPy
description: Learn how to build an AI puzzle solver using DSPy and Dagster
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/integrations/dspy.png
tags: [code-example]
canonicalUrl: '/examples/dspy'
slug: '/examples/dspy'
---

In this example, you'll build an AI system that solves [NYT Connections puzzles](https://www.nytimes.com/games/connections) that:

- Loads and process Connections puzzle data
- Uses [DSPy](https://dspy.ai/) for structured reasoning
- Optimize the solver using MIPROv2 automatic optimization
- Evaluate puzzle-solving performance with custom metrics
- Deploy and monitor the AI system in production

## Prerequisites

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.9+ installed on your system. Refer to the [Installation guide](/getting-started/installation) for information.
- Understanding of language models and AI pipelines
- Basic knowledge of the NYT Connections puzzle format

## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Clone the [Dagster repo](https://github.com/dagster-io/dagster) and navigate to the project:

   ```bash
   cd examples/docs_projects/project_dspy
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

4. Ensure the following environments have been populated in your .env file. Start by copying the template:

   ```bash
   cp .env.example .env
   ```

   Then populate the fields.

## Step 2: Launch the Dagster webserver

To make sure Dagster and its dependencies were installed correctly, navigate to the project root directory and start the Dagster webserver:

```bash
dg dev
```

Navigate to [http://127.0.0.1:3000](http://127.0.0.1:3000) to view the Dagster UI.

## Next steps

- Continue this example with [puzzle data ingestion](/examples/full-pipelines/dspy/data-ingestion)
