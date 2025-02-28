---
title: 'Components ETL pipeline tutorial'
sidebar_position: 10
---

## Setup

### 1. Install project dependencies

:::info Prerequisites

To complete this tutorial, you must [install `uv` and `dg`](/guides/labs/components/index.md#installation).

:::

First, install [`duckdb`](https://duckdb.org/docs/installation/?version=stable&environment=cli&platform=macos&download_method=package_manager) for a local database and [`tree`](https://oldmanprogrammer.net/source.php?dir=projects/tree/INSTALL) to visualize project structure:

<Tabs>

<TabItem value="mac" label="Mac">

<CliInvocationExample contents="brew install duckdb tree" />

</TabItem>

<TabItem value="windows" label="Windows">

See the [`duckdb`](https://duckdb.org/docs/installation/?version=stable&environment=cli&platform=win&download_method=package_manager) Windows installation instructions and [`tree`](https://oldmanprogrammer.net/source.php?dir=projects/tree/INSTALL) installation instructions.

</TabItem>

<TabItem value="linux" label="Linux">

See the [`duckdb`](https://duckdb.org/docs/installation/?version=stable&environment=cli&platform=linux&download_method=direct&architecture=x86_64) and [`tree`](https://oldmanprogrammer.net/source.php?dir=projects/tree/INSTALL) Linux installation instructions.

</TabItem>

</Tabs>

:::note

`tree` is optional and is only used to produce a nicely formatted representation of the project structure on the comand line. You can also use `find`, `ls`, `dir`, or any other directory listing command.

:::


### 2. Scaffold a new project

After installing dependencies, scaffold a components-ready project:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/2-scaffold.txt"  />

The `dg scaffold project` command builds a project at `jaffle-platform` and initializes a new Python
virtual environment inside it. When you use `dg`'s default environment management behavior, you won't need to worry about activating this virtual environment yourself.

To learn more about the files, directories, and default settings in a project scaffolded with `dg scaffold project`, see "[Creating a project with components](/guides/labs/components/building-pipelines-with-components/creating-a-project-with-components#project-structure)".

## Ingest data

### 1. Add the Sling component type to your environment

To ingest data, you must set up [Sling](https://slingdata.io/). However, if you list the available component types in your environment at this point, the Sling component won't appear, since the basic `dagster-components` package that was installed when you scaffolded your project doesn't include components for specific integrations (like Sling):

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/7-dg-list-component-types.txt" />

To make the Sling component available in your environment, install the `sling` extra of `dagster-components`:

<CliInvocationExample contents="uv add 'dagster-components[sling]'" />

:::note

`dg` always operates in an isolated environment, but it is able to access the set of component types available in your project environment because it attempts to resolve a project root whenever it is run. If `dg` finds a `pyproject.toml` file with a `tool.dg.is_project = true` setting, then it will expect a `uv`-managed virtual environment to be present in the same directory. (This can be confirmed by the presence of a `uv.lock` file.)

When you run commands like `dg list component-type` , `dg` obtains the results by identifying the in-scope project environment and querying it. In this case, the project environment was set up as part of the `dg scaffold project` command.

:::

### 2. Confirm availability of the Sling component type

To confirm that the `dagster_components.sling_replication` component type is now available, run the `dg list component-type` command again:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/8-dg-list-component-types.txt" />

### 3. Create a new instance of the Sling component

Next, create a new instance of this component type:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/9-dg-scaffold-sling-replication.txt" />

This adds a component instance to the project at `jaffle_platform/defs/ingest_files`:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/10-tree-jaffle-platform.txt" />

A single file, `component.yaml`, was created in the component folder. The `component.yaml` file is common to all Dagster components, and specifies the component type and any parameters used to scaffold definitions from the component at runtime.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/11-component.yaml" language="YAML" title="jaffle-platform/jaffle_platform/defs/ingest_files/component.yaml"/>

Right now the parameters define a single "replication"-- this is a Sling concept that specifies how data should be replicated from a source to a target. The details are specified in a `replication.yaml` file that is read by Sling. This file does not yet exist-- we are going to create it shortly.

:::note
The `path` parameter for a replication is relative to the same folder containing component.yaml. This is a convention for components.
:::

### 4. Set up DuckDB

Set up and test DuckDB:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/12-sling-setup-duckdb.txt" />

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/13-sling-test-duckdb.txt" />

### 5. Download files for Sling source

Next, you will need to download some files locally to use your Sling source, since Sling doesn't support reading from the public internet:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/14-curl.txt" />

Finally, create a `replication.yaml` file that references the downloaded files:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/15-replication.yaml" language="YAML" title="jaffle-platform/jaffle_platform/defs/ingest_files/replication.yaml" />

### 6. View and materialize assets in the Dagster UI

Load your project in the Dagster UI to see what you've built so far. To materialize assets and load tables in the DuckDB instance, click **Materialize All**:

<CliInvocationExample contents="dg dev" />

![](/images/guides/build/projects-and-components/components/sling.png)

Verify the DuckDB tables on the command line:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/16-duckdb-select.txt" />

## Transform data

To transform the data, you will need to download a sample dbt project from GitHub and use the data ingested with Sling as an input for the dbt project.

### 1. Clone a sample dbt project from GitHub

First, clone the project and delete the embedded git repo:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/17-jaffle-clone.txt" />

### 2. Install the dbt project component type

To interface with the dbt project, you will need to instantiate a Dagster dbt project component. To access the dbt project component type, install `dagster-components[dbt]` and `dbt-duckdb`:

<CliInvocationExample contents="uv add 'dagster-components[dbt]' dbt-duckdb" />

To confirm that the `dagster_components.dbt_project` component type is now available, run `dg list component-type`:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/18-dg-list-component-types.txt" />


### 3. Scaffold a new instance of the dbt project component

Next, scaffold a new instance of the `dagster_components.dbt_project` component, providing the path to the dbt project you cloned earlier as the `project_path` scaffold parameter:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/19-dg-scaffold-jdbt.txt"/>

This creates a new component instance in the project at `jaffle_platform/defs/jdbt`. To see the component configuration, open `component.yaml` in that directory:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/20-component-jdbt.yaml" language="YAML" title="jaffle-platform/jaffle_platform/defs/jdbt/component.yaml" />

### 4. Update the dbt project component configuration

Let’s see the project in the Dagster UI:

<CliInvocationExample contents="dg dev" />

![](/images/guides/build/projects-and-components/components/dbt-1.png)

You can see that there appear to be two copies of the `raw_customers`, `raw_orders`, and `raw_payments` tables. If you click on the assets, you can see their full asset keys. The keys generated by the dbt component are of the form `main/*`, whereas the keys generated by the Sling component are of the form `target/main/*`.

We need to update the configuration of the `dagster_components.dbt_project` component to match the keys generated by the Sling component. Update `components/jdbt/component.yaml` with the configuration below:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/21-project-jdbt-incorrect.yaml" language="YAML" title="jaffle-platform/jaffle_platform/defs/jdbt/component.yaml" />

You might notice the typo in the above file--after updating a component file, it's useful to validate that the changes match the component's schema. You can do this by running `dg check yaml`:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/22-dg-component-check-error.txt" />

You can see that the error message includes the filename, line number, and a code snippet showing the exact nature of the error. Let's fix the typo:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/23-project-jdbt.yaml" language="YAML" title="jaffle-platform/jaffle_platform/defs/jdbt/component.yaml" />

Finally, run `dg check yaml` again to validate the fix:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/24-dg-component-check.txt" />

Reload the project in Dagster UI to verify that the keys load properly:

![](/images/guides/build/projects-and-components/components/dbt-2.png)

Now the keys generated by the Sling and dbt project components match, and the asset graph is correct. To materialize the new assets defined via the dbt project component, click **Materialize All**.

To verify the fix, you can view a sample of the newly materialized assets in DuckDB from the command line:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/25-duckdb-select-orders.txt" />

## Automate the pipeline

### 1. Automate Sling ingestion

Now that you've defined some assets, you can automate them to keep them up to date by using [declarative automation](/guides/automate/declarative-automation) directly in the `component.yaml` file.

Navigate to `defs/ingest_files/component.yaml` and add the `automation_condition` below to automatically pull in data with Sling every day:

```yaml create=jaffle_platform/defs/ingest_files/component.yaml title="jaffle-platform/jaffle_platform/defs/ingest_files/component.yaml"
type: dagster_components.dagster_sling.SlingReplicationCollectionComponent

attributes:
  replications:
    - path: replication.yaml
  asset_attributes:
    - target: "*"
	    attributes:
        automation_condition: "{{ automation_condition.on_cron('@daily') }}"
        metadata:
          automation_condition: "on_cron(@daily)"
```

### 2. Automate dbt transformation

Next, update the dbt project so it executes after the Sling replication runs. Navigate to `components/jdbt/component.yaml` and add the `automation_condition` below:

```yaml create=jaffle_platform/defs/jdbt/component.yaml title="jaffle-platform/jaffle_platform/defs/jdbt/component.yaml"
type: dagster_components.dagster_dbt.DbtProjectComponent

attributes:
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

## Next steps

To continue your journey with components, you can [add more components to your project](/guides/labs/components/building-pipelines-with-components/adding-components) or learn how to [manage multiple projects with components](/guides/labs/components/managing-multiple-projects).
