---
title: Prompt engineering with Anthropic
description: Learn how to do prompt engineering
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/integrations/anthropic.svg
tags: [code-example]
canonicalUrl: '/examples/full-pipelines/prompt-engineering'
slug: '/examples/full-pipelines/prompt-engineering'
---

In this example, you'll build a pipeline with Dagster that:

- Takes an input question
- Generates prompts to use with [Anthropic](https://www.anthropic.com)
- Validates outputs of AI models and passes outputs across assets

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.9+ installed on your system. For more information, see the [Installation guide](/getting-started/installation).

</details>

## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Clone the the [Dagster repo](https://github.com/dagster-io/dagster) and navigate to the project:

   ```bash
   cd examples/docs_projects/project_prompt_eng
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

- Continue this example with [prompts](/examples/full-pipelines/prompt-engineering/prompts)
