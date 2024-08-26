---
title: 'Creating domain-specific languages with asset factories'
sidebar_position: 60
sidebar_label: 'Creating domain-specific languages'
---

Often times in data engineering, you'll find yourself needing to create a large number of similar assets. For example, you might have a set of tables in a database that all have the same schema, or a set of files in a directory that all have the same format. In these cases, it can be helpful to create a factory that generates these assets for you.

Additionally, you might be serving stakeholders who are not familiar with Python or Dagster, and would prefer to interact with your assets using a domain-specific language (DSL) built on top of a configuration language such as YAML.

You can solve both of these problems using the **asset factory pattern**. In this guide, we'll show you how to build a simple asset factory in Python, and then how to build a DSL on top of it.

## What you'll learn

- Building a simple asset factory in Python
- Driving your asset factory with YAML
- Improving usability with Pydantic and Jinja

---

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- A basic understanding of Dagster and assets. See the [Quick Start](/tutorial/quick-start) tutorial for an overview.
- High-level familiarity with Dagster's [Resources system](/concepts/resources)
- Familiarity with SQL, YAML and AWS S3.
- Basic familiarity with [Pydantic](https://docs.pydantic.dev/latest/) and [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/).
</details>

---

## Building a simple asset factory in Python

Let's imagine a team that has to perform the same repetitive ETL task often: they download a CSV file from S3, run a basic SQL query on it, and then upload the result as a new file back to S3.

To start, let's install the required dependencies:

```shell
pip install dagster dagster-aws duckdb
```

Next, here's how you might define a simple asset factory in Python to automate this ETL process:

<CodeExample filePath="guides/data-modeling/asset-factories/python-asset-factory.py" language="python" title="Basic Python asset factory" />

As you can see, the asset factory pattern is basically just a function that takes in some configuration and returns `dg.Definitions`.

## Driving your asset factory with YAML

Now, let's say that the team wants to be able to configure the asset factory using a YAML file instead of Python. Here's an example of how we might want the YAML file to look:

<CodeExample filePath="guides/data-modeling/asset-factories/etl_jobs.yaml" language="yaml" title="Example YAML config" />

Implementing this is straightforward if we build on the previous example. First, let's install PyYAML:

```shell
pip install pyyaml
```

Next, we parse the YAML file and use it to create the S3 resource and the ETL jobs:

<CodeExample filePath="guides/data-modeling/asset-factories/simple-yaml-asset-factory.py" language="python" title="Basic YAML asset factory" />

## Improving usability with Pydantic and Jinja

There are two problems with the simple approach described above:

1. The YAML file is not type-checked, so it's easy to make mistakes that will cause cryptic `KeyError`s.
2. The YAML file contains secrets right in the file. Instead, it should reference environment variables.

To solve these problems, we can use Pydantic to define a schema for the YAML file, and Jinja to template the YAML file with environment variables.

Here's what the new YAML file might look like. Note how we are using Jinja templating to reference environment variables:
<CodeExample filePath="guides/data-modeling/asset-factories/etl_jobs_with_jinja.yaml" language="yaml" title="Example YAML config with Jinja" />

And here is the Python implementation:

<CodeExample filePath="guides/data-modeling/asset-factories/advanced-yaml-asset-factory.py" language="python" title="Advanced YAML asset factory" />
