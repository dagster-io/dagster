---
title: 'Using Environment Variables in Components'
sidebar_position: 100
---


import Preview from '@site/docs/partials/\_Preview.md';

<Preview />


It's common to want to configure components depending on the environment in which they are run. `dg` and components make it easy to configure this behavior.


## Setting up a components project with dbt

We start with an empty Dagster components project. Let's begin by pulling down a sample dbt project from GitHub:

<CodeExample path="docs_snippets/docs_snippets/guides/dg/using-env/1-jaffle-clone.txt" language="bash" />

Next, we'll install the `dagster-components[dbt]` package:

<CliInvocationExample contents="uv add 'dagster-components[dbt]' dbt-duckdb" />

To confirm that the `dagster_components.dbt_project` component type is now available, run `dg list component-type`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/2-dg-list-component-types.txt" />

Next, we'll scaffold a new dbt component to represent the dbt project as assets:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/3-dg-scaffold-jdbt.txt" />

We can use `dg check yaml` to validate that the component is configured correctly:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/4-dg-component-check.txt" />

We can then generate the manifest, and take a look at the assets we've configured:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/5-dbt-parse.txt" />

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/6-dg-list-defs.txt" />

## Configuring the component to use environment variables
We'd like our asset keys to reflect the database and schema in which the tables are materialized. We can configure our `component.yaml` to do this, relying on environment variables to vary the schema based on our environment:

<CodeExample path="docs_snippets/docs_snippets/guides/dg/using-env/7-project-jdbt.yaml" language="yaml" />

If we run `dg check yaml`, we see that we need to encode our environment dependency in the component file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/8-dg-component-check.txt" />

If we pass the `--fix-env-requirements` flag to `dg check yaml`, the component file will automatically be updated to include the environment variable:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/9-dg-component-check.txt" />

Now, we get an error that the environment variable is not set. We'll add it to our `.env` file:
<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/10-inject-env.txt" />

Let's run `dg check yaml` once more, and we see that the component file is now valid:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/11-dg-component-check-fixed.txt" />

We can employ `dg env list` to see that our env var has been configured, and is being used by our dbt component:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/12-dg-env-list.txt" />

And we can see that the assets have been configured to use the proper schema:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/13-dg-list-defs.txt" />

## Using environment variables with Dagster Plus

We can use environment variables to configure secrets for Dagster Plus. Let's say we want to now deploy our dbt project to our production environment.

First, we'll authenticate with Dagster Plus:

<CliInvocationExample contents="dg plus login" />

If we run `dg env list`, we now see additional columns showing whether the environment variable is set for each location:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/14-dg-env-list.txt" />

We can use `dg plus env add` to configure the environment variable in Dagster Plus. First, we can push up our local environment variable to the `dev` scope, so that
other developers can use it in their local environments:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/15-dg-plus-env-add.txt" />

If we run `dg env list` again, we see that the environment variable is now set for the `dev` scope:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/16-dg-env-list.txt" />

Finally, we can push up the environment variable to the `full` and `branch` scopes:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/17-dg-plus-env-add.txt" />

If we run `dg env list` again, we see that the environment variable is now set for all scopes:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/18-dg-env-list.txt" />

We can go ahead and deploy our project to production:

<CliInvocationExample contents="dg deploy" />
