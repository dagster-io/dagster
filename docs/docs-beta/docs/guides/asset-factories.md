---
title: 'Creating domain-specific languages with asset factories'
sidebar_position: 60
sidebar_label: 'Asset factories'
---

Often in data engineering, you'll find yourself needing to create a large number of similar assets. For example:

- A set of database tables all have the same schema
- A set of files in a directory all have the same format

It's also possible you're serving stakeholders who aren't familiar with Python or Dagster. They may prefer interacting with assets using a domain-specific language (DSL) built on top of a configuration language such as YAML.

The asset factory pattern can solve both of these problems.

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Familiarity with:
  - [Assets](/guides/data-assets)
  - [Resources](/concepts/resources)
  - SQL, YAML and Amazon Web Services (AWS) S3
  - [Pydantic](https://docs.pydantic.dev/latest/) and [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/)
- A Python virtual environment with the following dependencies installed:

   ```bash
   pip install dagster dagster-aws duckdb pyyaml pydantic
   ```
</details>

## Building an asset factory in Python

Let's imagine a team that often has to perform the same repetitive ETL task: download a CSV file from S3, run a basic SQL query on it, and then upload the result as a new file back to S3.

To automate this process, you might define an asset factory in Python like the following:

<CodeExample filePath="guides/data-modeling/asset-factories/python-asset-factory.py" language="python" />

The asset factory pattern is essentially a function that takes in some configuration and returns `dg.Definitions`.

## Configuring an asset factory with YAML

Now, the team wants to be able to configure the asset factory using YAML instead of Python, with a file like this:

<CodeExample filePath="guides/data-modeling/asset-factories/etl_jobs.yaml" language="yaml" title="etl_jobs.yaml" />

To implement this, parse the YAML file and use it to create the S3 resource and ETL jobs:

<CodeExample filePath="guides/data-modeling/asset-factories/simple-yaml-asset-factory.py" language="python" />

## Improving usability with Pydantic and Jinja

There are a few problems with the current approach:

1. **The YAML file isn't type-checked**, so it's easy to make mistakes that will cause cryptic `KeyError`s
2. **The YAML file contains secrets**. Instead, it should reference environment variables.

To solve these problems, you can use Pydantic to define a schema for the YAML file and Jinja to template the YAML file with environment variables.

Here's what the new YAML file might look like. Note how Jinja templating is used to reference environment variables:

<CodeExample filePath="guides/data-modeling/asset-factories/etl_jobs_with_jinja.yaml" language="yaml" title="etl_jobs.yaml" />

And the Python implementation:

<CodeExample filePath="guides/data-modeling/asset-factories/advanced-yaml-asset-factory.py" language="python" />

## Next steps

TODO
