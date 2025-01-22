---
title: RAG
description: Learn how to build a RAG system
last_update:
   author: Dennis Hume
sidebar_position: 10
---

:::
To see a live coding example of this tutorial [YouTube Video](https://www.youtube.com/watch?v=MHwwKfCXwDA)
:::

# RAG

In this tutorial, you'll build a pipeline with Dagster that:

- Loads data from Github and Documentation site
- Translates the data into embeddings and tags metadata
- Stores the data in a vector database
- Retrieves relevant information to answer ad hoc questions

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.9+ installed on your system. Refer to the [Installation guide](/getting-started/installation) for information.
</details>


## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Within the Dagster repo, navigate to the project:

   ```bash
   cd examples/project_ask_ai_dagster
   ```

2. Create and activate a virtual environment:

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

3. Install Dagster and the required dependencies:

   ```bash
   uv pip install -e ".[dev]"
   ```

## Step 2: Launch the Dagster webserver

To make sure Dagster and its dependencies were installed correctly, navigate to the project root directory and start the Dagster webserver:

followed by a bash code snippet for 

```bash
dagster dev
```

## Next steps

- Continue this tutorial with [ingestion](ingestion)