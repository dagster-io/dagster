---
title: 'Using environment variables with components'
description: Use environment variables to configure components locally and in Dagster+.
sidebar_position: 100
---

With `dg` and components, you can easily configure components depending on the environment in which they are run. To demonstrate this, we'll walk through setting up an example ELT pipeline with a Sling component which reads Snowflake credentials from environment variables.

:::tip

For more information on using environment variables with non-component Dagster code, see [Using environment variables and secrets in Dagster code](/guides/operate/configuration/using-environment-variables-and-secrets).

:::

## 1. Create a new Dagster components project

First, we'll set up a basic ELT pipeline using Sling in an empty Dagster components project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/1-dg-init.txt" />

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/2-activate-venv.txt" />

We'll install `dagster-sling` and scaffold an empty Sling connection component:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/3-uv-add-sling.txt" />

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/4-dg-list-components.txt" />
</WideContent>

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/5-dg-scaffold-sling.txt" />

## 2. Use environment variables in a component

Next, we will configure a Sling connection that will sync a local CSV file to a Snowflake database, with credentials provided with environment variables:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/6-curl.txt" />

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/using-env/7-replication.yaml"
  language="yaml"
  title="src/ingestion/defs/ingest_files/replication.yaml"
/>

We will use the `env` function to template credentials into Sling configuration in our `defs.yaml` file. Running `dg check yaml` will highlight that we
need to explicitly encode these environment dependencies at the bottom of the file:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/using-env/8-defs.yaml"
  language="yaml"
  title="src/ingestion/defs/ingest_files/defs.yaml"
/>

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/9-dg-component-check.txt" />

After adding the environment dependencies, running `dg check yaml` again will confirm that the file is valid:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/using-env/10-component-with-env-deps.yaml"
  language="yaml"
  title="src/ingestion/defs/ingest_files/defs.yaml"
/>

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/11-dg-component-check-fixed.txt" />

Next, you can invoke `dg list env`, which shows all environment variables configured or used by components in the project. Here we can see all of the Snowflake credentials we must configure in our shell or `.env` file to run our project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/12-dg-list-env.txt" />

You can edit the `.env` file in your project root to specify environment variables for Dagster to use when running the project locally. You can run `dg list env` again to see that they are now set:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/13-inject-env.txt" />

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/14-dg-list-env.txt" />

## 3. Configure environment variables for components in Dagster+ (Optional)

If you are using Dagster+, you can also use the `dg` CLI to push environment variables to your deployment so that your code is ready to run in a production setting.

First, you will need to authenticate with Dagster+:

<CliInvocationExample contents="dg plus login" />

The `dg list env` command will now automatically show what scopes environment variables are configured for, in your configured deployment:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/15-dg-env-list.txt" />

From here, you can use the `dg plus create env` command to push environment variables to your deployment. The `--from-local-env` flag will read the environment variables from your local shell or `.env` file.

### Configure local environment variables

To enable the rest of your team to run your project locally, you can run the following command to push each Snowflake credential to the `local` scope:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/16-dg-plus-env-add.txt" />

Running `dg list env` again will confirm that the environment variables have been pushed to your deployment:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/17-dg-env-list.txt" />

Now that `local` scope environment variables have been pushed to your deployment, your teammates can pull them into a `.env` file for local use:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/18-dg-env-pull.txt" />

### Configure production environment variables

Finally, you can configure a different set of production environment variables for your Dagster+ deployment:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/19-dg-plus-env-add.txt" />

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/using-env/20-dg-env-list.txt" />
