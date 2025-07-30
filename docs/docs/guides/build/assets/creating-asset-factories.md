---
description: Learn to create Dagster asset factories in Python using YAML configuration, Pydantic for schema validation, and Jinja2 for templating, optimizing ETL processes.
sidebar_position: 500
title: Creating asset factories
---

Often in data engineering, you'll find yourself needing to create a large number of similar assets. For example:

- A set of database tables all have the same schema
- A set of files in a directory all have the same format

It's also possible you're serving stakeholders who aren't familiar with Python or Dagster. They may prefer interacting with assets using a domain-specific language (DSL) built on top of a configuration language such as YAML.

The asset factory pattern can solve both of these problems.

:::note

This article assumes familiarity with:
  - [Assets](/guides/build/assets/defining-assets)
  - [Resources](/guides/build/external-resources)
  - SQL, YAML, and Amazon Web Services (AWS) S3
  - [Pydantic](https://docs.pydantic.dev/latest) and [Jinja2](https://jinja.palletsprojects.com/en/3.1.x)

:::

<details>
  <summary>Prerequisites</summary>

To run the example code in this article, you'll need:

- Install the necessary Python libraries:

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">
      Install the required dependencies:

         ```shell
         uv add dagster dagster-aws duckdb pyyaml pydantic
         ```

   </TabItem>

   <TabItem value="pip" label="pip">
      Install the required dependencies:

         ```shell
         pip install dagster dagster-aws duckdb pyyaml pydantic
         ```

   </TabItem>
</Tabs>

</details>

## Building an asset factory in Python

Let's imagine a team that often has to perform the same repetitive ETL task: download a CSV file from S3, run a basic SQL query on it, and then upload the result as a new file back to S3.

To automate this process, you might define an asset factory in Python like the following:

<CodeExample path="docs_snippets/docs_snippets/guides/data-modeling/asset-factories/python-asset-factory.py" language="python" title="src/<project_name>/defs/assets.py" />

The asset factory pattern is essentially a function that takes in some configuration and returns `dg.Definitions`.

## Configuring an asset factory with YAML

Now, the team wants to be able to configure the asset factory using YAML instead of Python, with a file like this:

<CodeExample path="docs_snippets/docs_snippets/guides/data-modeling/asset-factories/etl_jobs.yaml" language="yaml" title="etl_jobs.yaml" />

To implement this, parse the YAML file and use it to create the S3 resource and ETL jobs:

<CodeExample path="docs_snippets/docs_snippets/guides/data-modeling/asset-factories/simple-yaml-asset-factory.py" language="python" title="src/<project_name>/defs/assets.py" />

## Improving usability with Pydantic and Jinja

There are a few problems with the current approach:

1. **The YAML file isn't type-checked**, so it's easy to make mistakes that will cause cryptic `KeyError`s
2. **The YAML file contains secrets**. Instead, it should reference environment variables.

To solve these problems, you can use Pydantic to define a schema for the YAML file and Jinja to template the YAML file with environment variables.

Here's what the new YAML file might look like. Note how Jinja templating is used to reference environment variables:

<CodeExample path="docs_snippets/docs_snippets/guides/data-modeling/asset-factories/etl_jobs_with_jinja.yaml" language="yaml" title="etl_jobs.yaml" />

And the Python implementation:

<CodeExample path="docs_snippets/docs_snippets/guides/data-modeling/asset-factories/advanced-yaml-asset-factory.py" language="python" title="src/<project_name>/defs/assets.py" />
