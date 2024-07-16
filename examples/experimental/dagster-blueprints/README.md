# dagster-blueprints

Dagster’s core definition Python APIs are infinitely flexible. This flexibility is vital for developers facing a wide set of data engineering problems. However, it’s also often dizzying and intimidating to people who need to contribute to data pipelines, but aren’t full time data engineers or experts in Dagster. For example, a data analyst who wants to pull in some data from a new data source, or a scientist who wants to wire up some preexisting shell scripts into a pipeline.

"Blueprints" is a layer built on top of these APIs, that helps offer guard rails and simpler interfaces for contributing to data pipelines. Blueprints are intended to be used for common repetitive pipeline authoring tasks, such as:

- Configuring a data sync of a common type
- Putting a shell script on a schedule
- Putting a Databricks notebook on a schedule

A blueprint is a simple blob of data that describes how to construct one or more Dagster definitions. Because blueprints are simple blobs of data, they can be authored in YAML. In the future, they'll also be able to be authored in JSON, and perhaps even in Dagster's UI.

![image](https://github.com/dagster-io/dagster/assets/654855/d65c9db3-cf1f-4a0f-a5aa-63be36e99076)

Blueprints are intended to be heavily customized within an organization. While Dagster provides some blueprint types out of the box, the expectation is that data platform engineers will write Python code to curate and develop the set of blueprint types that their stakeholders have access to.

![image](https://github.com/dagster-io/dagster/assets/654855/660983f4-a581-4094-8f66-c8a95e4299c3)

## Blueprints vs. parsing YAML on your own

Why use Blueprints when you can write your own code to parse YAML and generate Dagster definitions?

- Schematized – Blueprints are typed using Pydantic classes. This enables the Dagster blueprints library to offer utilities that streamline YAML/JSON development:
  - Generate configuration for VS Code that offers typeahead and type-checking for YAML.
  - High quality errors when values don’t conform to types, linked to positions in the source YAML file.
- Code references – Blueprints automatically attach metadata that link definitions to the YAML they were generated from.
- Built-ins – take advantage of built-in blueprint types and use them seamlessly alongside your own custom types.

## How to try out Blueprints

### Install

Install the dagster-blueprints package:

```python
pip install dagster-blueprints
```

### Try out one of the examples:

- [Built-in blueprints](examples/builtin-blueprints)
- [Custom blueprints](examples/custom-blueprints)
