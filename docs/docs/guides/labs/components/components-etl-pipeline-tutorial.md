---
title: 'Components ETL pipeline tutorial'
sidebar_position: 10
---

## Setup

### Install project dependencies

If you have not already done so, follow the [steps to install `uv` and `dg`](/guides/labs/components/index.md#installation).

Next, install the tools used in this tutorial. We use [`duckdb`](https://duckdb.org/docs/installation/?version=stable&environment=cli&platform=macos&download_method=package_manager) for a local database, and [`tree`](https://oldmanprogrammer.net/source.php?dir=projects/tree/INSTALL) to visualize project structure. `tree` is optional and is only used to produce an easily understandable representation of the project structure on the comand line. `find`, `ls` or any other directory listing command will also work.

<CliInvocationExample contents="brew install duckdb tree" />

:::note

If you are not in a Mac environment, use the links above to see the installation instructions for your environment.

:::

### Scaffold a new code location

After installing dependencies, scaffold a Components-ready code location for the project:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/2-scaffold.txt"  />

This command builds a code location at `jaffle-platform` and initializes a new Python
virtual environment inside of it. When using `dg`'s default environment
management behavior, you won't need to worry about activating this virtual environment yourself.

To learn more about the files, directories, and default settings in a code location scaffolded with Components, see "[Creating a code location with Components](/guides/labs/components/building-pipelines-with-components/creating-a-code-location-with-components#overview-of-files-and-directories)

## Ingest data

### Add the Sling Component

First, you will need to set up Sling. If you query the available Component types in your environment at this point, you won't see anything Sling-related:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/7-dg-list-component-types.txt" />

This is because the basic `dagster-components` package (which was installed when we scaffolded our code location) doesn't include Components for specific integrations (like Sling). We can get access to a Sling Component by installing the `sling` extra of `dagster-components`:

<CliInvocationExample contents="uv add 'dagster-components[sling]'" />

:::note

`dg` always operates in an isolated environment, but it is able to access the set of Component types available in your project environment, because under the hood, `dg` attempts to resolve a project root whenever it is run. If it finds a `pyproject.toml` file with a `tool.dg.is_code_location = true` setting, then it will expect a `uv`-managed virtual environment to be present in the same directory (this can be confirmed by the presence of a `uv.lock` file). When you run commands like `dg component-type list`, `dg` obtains the results by identifying the in-scope project environment and querying it. In this case, the project environment was set up as part of the `dg code-location scaffold` command.

:::

Run the TODO command again to confirm that the `dagster_components.sling_replication` Component type is now available:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/8-dg-list-component-types.txt" />

Next, create a new instance of this Component type:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/9-dg-scaffold-sling-replication.txt" />

This adds a component instance to the project at `jaffle_platform/components/ingest_files`:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/10-tree-jaffle-platform.txt" />

A single file, `component.yaml`, was created in the Component folder. The `component.yaml` file is common to all Dagster components, and specifies the Component type and any parameters used to scaffold definitions from the Component at runtime.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/11-component.yaml" language="YAML" title="jaffle-platform/jaffle_platform/components/ingest_files/component.yaml"/>

Right now the parameters define a single "replication"-- this is a Sling concept that specifies how data should be replicated from a source to a target. The details are specified in a `replication.yaml` file that is read by Sling. This file does not yet exist-- we are going to create it shortly.

:::note
The `path` parameter for a replication is relative to the same folder containing component.yaml. This is a convention for components.
:::

### Set up DuckDB

Set up and test DuckDB:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/12-sling-setup-duckdb.txt" />

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/13-sling-test-duckdb.txt" />

### Download files for Sling source

Next, you will need to download some files locally to use your Sling source, since Sling doesn't support reading from the public internet:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/14-curl.txt" />

Finally, create a `replication.yaml` file that references the downloaded files:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/15-replication.yaml" language="YAML" title="jaffle-platform/jaffle_platform/components/ingest_files/replication.yaml" />

### View and materialize assets in the Dagster UI

Let's load up our code location in the Dagster UI to see what we've got:

<CliInvocationExample contents="uv run dagster dev # will be dg dev in the future" />

![](/images/guides/build/projects-and-components/components/sling.png)

Click "Materialize All", and we should now have tables in the DuckDB instance. Let's verify on the command line:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/16-duckdb-select.txt" />

## Transform data

### Clone a sample dbt project from GitHub

To transform the data, you will need to download clone a sample dbt project from GitHub. You will use the data ingested with Sling as an input for the dbt project. Follow the steps below to clone the project and delete the embedded git repo:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/17-jaffle-clone.txt" />

### Install the dbt project Component type

To interface with the dbt project, you will need to instantiate a Dagster dbt project Component. To access the dbt project Component type, install `dagster-components[dbt]` and `dbt-duckdb`:

<CliInvocationExample contents="uv add 'dagster-components[dbt]' dbt-duckdb" />

Run the TODO command to confirm that the `dagster_components.dbt_project` Component type is now available:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/18-dg-list-component-types.txt" />

You can access detailed information about a Component type with the `dg component-type info` command:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/19-dg-component-type-info.txt" />

The output of `dg component-type info` shows the parameters (in JSON schema format) for both Component generation and runtime loading of the Component. (The runtime parameters have been truncated here due to length.)

### Scaffold a new instance of the dbt project Component

Next, scaffold a new instance of the `dagster_components.dbt_project` component, providing the path to the dbt project you cloned earlier as the `project_path` scaffold paramater:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/20-dg-scaffold-jdbt.txt"/>

This creates a new Component instance in the project at `jaffle_platform/components/jdbt`. Open `component.yaml` in that directory and you'll see:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/21-component-jdbt.yaml" language="YAML" title="jaffle-platform/jaffle_platform/components/jdbt/component.yaml" />

### Update the dbt project Component configuration

Let’s see the project in the Dagster UI:

<CliInvocationExample contents="uv run dagster dev" />

![](/images/guides/build/projects-and-components/components/dbt-1.png)

You can see at first glance that there appear to be two copies of the `raw_customers`, `raw_orders`, and `raw_payments` tables. This isn't right-- if you click on the assets you can see their full asset keys. The keys generated by the DBT component are of the form `main/*` where the keys generated by the Sling component are of the form `target/main/*`. We need to update the configuration of the `dagster_components.dbt_project` component to match the keys generated by the Sling component. Update `components/jdbt/component.yaml` with the below:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/22-project-jdbt-incorrect.yaml" language="YAML" title="jaffle-platform/jaffle_platform/components/jdbt/component.yaml" />

You might notice the typo in the above file - after updating a component file, it's often useful to validate that the changes match the component's schema. You can do this by running `dg component check`:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/23-dg-component-check-error.txt" />

You can see that the error message includes the filename, line number, and a code snippet showing the exact nature of the error. Let's fix the typo:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/24-project-jdbt.yaml" language="YAML" title="jaffle-platform/jaffle_platform/components/jdbt/component.yaml" />

Finally, we can re-run `dg component check` to validate that our fix works:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/25-dg-component-check.txt" />


Reload the code location in Dagster UI and now the keys will connect properly:

![](/images/guides/build/projects-and-components/components/dbt-2.png)

Now the keys generated by the Sling and DBT project components match, and our
asset graph is correct. Click "Materialize All" to materialize the new assets
defined via the DBT project component. We can verify that this worked by
viewing a sample of the newly materialized assets from the command line:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/26-duckdb-select-orders.txt" />

## Automate the pipeline

### Automate Sling ingestion

Now that you've defined some assets, you can automate them to keep them up to date. You can do this using [declarative automation](/guides/automate/declarative-automation) directly in the `component.yaml` file. Navigate to `components/ingest_files/component.yaml` and add the `automation_condition` below to automatically pull in data with Sling every day:

```yaml create=jaffle_platform/components/ingest_files/component.yaml title="jaffle-platform/jaffle_platform/components/ingest_files/component.yaml"
type: dagster_components.sling_replication_collection

params:
  replications:
    - path: replication.yaml
  asset_attributes:
    - target: "*"
	    attributes:
        automation_condition: "{{ automation_condition.on_cron('@daily') }}"
        metadata:
          automation_condition: "on_cron(@daily)"
```

### Automate dbt transformation

Next, update the dbt project so it executes after the Sling replication runs. Navigate to `components/jdbt/component.yaml` and add the `automation_condition` below:

```yaml create=jaffle_platform/components/jdbt/component.yaml title="jaffle-platform/jaffle_platform/components/jdbt/component.yaml"
type: dagster_components.dbt_project

params:
  dbt:
    project_dir: ../../../dbt/jdbt
  asset_attributes:
    key: "target/main/{{ node.name }}"
  transforms:
    - target: "*"
      attributes:
        automation_condition: "{{ automation_condition.eager() }}"
      metadata:
        automation_condition: "eager"
```

Now the DBT project will update automatically after the Sling replication runs.

## Next steps

To continue your journey with Components, you can [add more Components to your project](/guides/labs/components/building-pipelines-with-components/adding-components-to-your-project) or learn how to [manage multiple code locations with Components](/guides/labs/components/managing-multiple-code-locations-with-components).