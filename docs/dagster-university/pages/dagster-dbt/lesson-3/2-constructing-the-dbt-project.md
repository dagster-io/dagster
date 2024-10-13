---
title: 'Lesson 3: Constructing the dbt project'
module: 'dagster_dbt'
lesson: '3'
---

# Constructing the dbt project

Independent of Dagster, running most dbt commands creates a set of files in a new directory called `target`. The most important file is the `manifest.json`. More commonly referred to as “the manifest file,” [this file](https://docs.getdbt.com/reference/artifacts/manifest-json) is a complete representation of your dbt project in a predictable format.

When Dagster builds your code location, it reads the manifest file to discover the dbt models and turn them into Dagster assets. There are a variety of ways to build the `manifest.json` file. However, we recommend using the `dbt parse` CLI command.

Change your current working directory to the `analytics`  folder and run the following command:

```bash
cd analytics # if you haven't set the directory yet
dbt parse
```

To confirm that a manifest file was generated, you should see two changes in your project:

1. A new directory at `analytics/target`, and
2. In the `target` directory, the `manifest.json` file

{% callout %}
> 💡 We recommend `dbt parse` since it doesn’t require a connection to your data warehouse to generate a manifest file, as opposed to commands like `dbt compile`. This means that `dbt parse` is fast and consistent across any environments you run it in, such as locally or during deployment.
> 
> If your dbt models use any [introspective queries](https://docs.getdbt.com/reference/commands/compile#interactive-compile), you may need to run `dbt compile` instead.
{% /callout %}

In Lesson 4, we’ll explore some options for deploying the manifest file more programmatically, along with some tips and tricks on having it regularly build your dbt manifest file during development.