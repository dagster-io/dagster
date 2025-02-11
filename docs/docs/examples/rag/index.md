---
title: Retrieval-Augmented Generation (RAG) with Pinecone
description: Learn how to build a RAG system
last_update:
   author: Dennis Hume
sidebar_position: 10
sidebar_custom_props:
  logo: images/integrations/pinecone.svg
---

:::note

To see [video of this example](https://www.youtube.com/watch?v=MHwwKfCXwDA)

:::

In this example, you'll build a pipeline with Dagster that:

- Loads data from GitHub and Documentation site
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

1. Clone the [Dagster repo](https://github.com/dagster-io/dagster) and navigate to the project:

   ```bash
   cd examples/docs_projects/project_ask_ai_dagster
   ```

2. Create and activate a virtual environment:

   <Tabs>
   <TabItem value="macos" label="MacOS">
   ```bash
   uv venv dagster_example
   source dagster_example/bin/activate
   ```
   </TabItem>
   <TabItem value="windows" label="Windows">
   ```bash
   uv venv dagster_example
   dagster_example\Scripts\activate
   ```
   </TabItem>
   </Tabs>

3. Install Dagster and the required dependencies:

   ```bash
   uv pip install -e ".[dev]"
   ```

## Step 2: Launch the Dagster webserver

To make sure Dagster and its dependencies were installed correctly, navigate to the project root directory and start the Dagster webserver:


```bash
dagster dev
```

## Next steps

- Continue this example with [sources](sources)
