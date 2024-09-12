---
title: 'Creating domain-specific languages with asset factories'
sidebar_position: 60
sidebar_label: 'Asset factories'
---

Often in data engineering, you'll find yourself needing to create a large number of similar assets. For example:

- A set of database tables all have the same schema
- A set of files in a directory all have the same format

Additionally, you may be serving stakeholders who aren't familiar with Python or Dagster. They may prefer interacting with assets using a domain-specific language (DSL) built on top of a configuration language such as YAML.

The asset factory pattern can solve both of these problems.

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- A basic understanding of Dagster and assets. See the [Quick Start](/getting-started/quickstart) tutorial for an overview.
- High-level familiarity with Dagster's [Resources system](/concepts/resources)
- Familiarity with SQL, YAML and Amazon Web Services (AWS) S3.
- Basic familiarity with [Pydantic](https://docs.pydantic.dev/latest/) and [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/).
- A Python virtual environment with the following dependencies installed: `dagster dagster-aws duckdb pyyaml pydantic`.
</details>

---

## Building an asset factory in Python

Let's imagine a team that has to perform the same repetitive ETL task often: they download a CSV file from S3, run a basic SQL query on it, and then upload the result as a new file back to S3.

After installing the required dependencies, here's how you might define an asset factory in Python to automate this ETL process:

<CodeExample filePath="guides/data-modeling/asset-factories/python-asset-factory.py" language="python" title="Basic Python asset factory" />

As you can see, the asset factory pattern is basically just a function that takes in some configuration and returns `dg.Definitions`.

## Driving your asset factory with YAML

Now, the team wants to be able to configure the asset factory using a YAML file instead of Python. Here's an example of how you might want the YAML file to look:

<CodeExample filePath="guides/data-modeling/asset-factories/etl_jobs.yaml" language="yaml" title="Example YAML config" />

This can be implemented by building on the previous example. Parse the YAML file and use it to create the S3 resource and the ETL jobs:

<CodeExample filePath="guides/data-modeling/asset-factories/simple-yaml-asset-factory.py" language="python" title="Basic YAML asset factory" />

## Improving usability with Pydantic and Jinja

There are two problems with the preceding approach:

1. The YAML file isn't type-checked, so it's easy to make mistakes that will cause cryptic `KeyError`s.
2. The YAML file contains secrets. Instead, it should reference environment variables.

To solve these problems, you can use Pydantic to define a schema for the YAML file, and Jinja to template the YAML file with environment variables.

Here's what the new YAML file might look like. Note how the Jinja templating is used to reference environment variables:

<CodeExample filePath="guides/data-modeling/asset-factories/etl_jobs_with_jinja.yaml" language="yaml" title="Example YAML config with Jinja" />

And here is the Python implementation:

<CodeExample filePath="guides/data-modeling/asset-factories/advanced-yaml-asset-factory.py" language="python" title="Advanced YAML asset factory" />
