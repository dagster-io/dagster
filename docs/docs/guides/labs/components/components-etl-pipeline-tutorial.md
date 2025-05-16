---
description: End-to-end tutorial with Dagster Components.
sidebar_position: 10
title: Components ETL pipeline tutorial
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';
import InstallUv from '@site/docs/partials/\_InstallUv.md';

<DgComponentsPreview />

## Setup

### 1. Install `duckdb` and `tree`

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

### 2. Install `dg`

Next, follow the [`dg` installation steps](/guides/labs/dg) to install the `dg` command line tool. `dg` allows you to quickly create a components-ready Dagster project.

### 3. Create a new Dagster project

After installing dependencies, create a components-ready Dagster project. The steps for creating a project will depend on your package manager/environment management strategy.

<Tabs groupId="package-manager">
    <TabItem value="uv" label="uv">

        First, run the command below, and respond yes to the prompt to run `uv sync` after scaffolding:

        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-a-uv-scaffold.txt" />

        Next, enter the directory and activate the virtual environment:

        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-b-uv-scaffold.txt" />

        :::note

        Running `uv sync` after creating a Dagster project creates a virtual environment and installs the dependencies listed in `pyproject.toml`, along with `jaffle-platform` itself as an [editable install](https://setuptools.pypa.io/en/latest/userguide/development_mode.html).

        :::
    </TabItem>
    <TabItem value="pip" label="pip">
        Because `pip` does not support global installations, you will need to install `dg` inside your Dagster project virtual environment. To do so, follow the commands below to create and enter a Dagster project directory, initialize and activate a virtual environment, and install the `dagster-dg` package into it:
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-a-pip-scaffold.txt" />
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-b-pip-scaffold.txt" />
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-c-pip-scaffold.txt" />
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-d-pip-scaffold.txt" />
        Next, run `dg scaffold project .` to create a new Dagster project in the current directory:
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-e-pip-scaffold.txt" />
        Finally, install the newly created project package into the virtual environment as an [editable install](https://setuptools.pypa.io/en/latest/userguide/development_mode.html):
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-f-pip-scaffold.txt" />
    </TabItem>

</Tabs>

To learn more about the files, directories, and default settings in a project created with `dg scaffold project`, see "[Creating a project with components](/guides/labs/dg/creating-a-project#project-structure)".

## Ingest data

### 1. Add the Sling component type to your environment

To ingest data, you will need to set up [Sling](https://slingdata.io/). To make the Sling component available in your environment, install the `dagster-sling` package:

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/8-uv-add-sling.txt" />
  </TabItem>
  <TabItem value="pip" label="pip">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/8-pip-add-sling.txt" />
  </TabItem>
</Tabs>

### 2. Confirm availability of the Sling component type

To confirm that the `dagster_sling.SlingReplicationCollectionComponent` component type is now available, run the `dg list plugins` command:

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/9-dg-list-plugins.txt" />
</WideContent>

### 3. Create a new instance of the Sling component

Next, create a new instance of the Sling component type:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/10-dg-scaffold-sling-replication.txt" />

This adds a Sling component instance called `ingest_files` to the `src/jaffle_platform/defs` directory of your project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/11-tree-jaffle-platform.txt" />

A single file, `component.yaml`, was created in the `ingest_files` directory. Every Dagster component has a `component.yaml` file that specifies the component type and any parameters used to scaffold definitions from the component at runtime:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/12-component.yaml"
  language="YAML"
  title="jaffle-platform/src/jaffle_platform/defs/ingest_files/component.yaml"
/>

Currently, the parameters in your Sling component `component.yaml` define a single `replication`, which is a Sling term that specifies how data should be replicated from a source to a target. The replication details are specified in a `replication.yaml` file that is read by Sling. You will create this file shortly.

:::note

The `path` parameter for a replication is relative to the directory that contains `component.yaml`. This is a convention for components.

:::

### 4. Download files for Sling source

Next, you will need to download some files locally to use your Sling source, since Sling doesn't support reading from the public internet:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/13-curl.txt" />

### 5. Set up the Sling to DuckDB replication

Once you have downloaded your Sling source files, update the `replication.yaml` file to reference them:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/14-replication.yaml"
  language="YAML"
  title="jaffle-platform/src/jaffle_platform/defs/ingest_files/replication.yaml"
/>

Next, modify the `component.yaml` file to tell the Sling component where replicated data with the `DUCKDB` target should be written:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/15-component-connections.yaml"
  language="YAML"
  title="jaffle-platform/src/jaffle_platform/defs/ingest_files/component.yaml"
/>

### 6. View and materialize assets in the Dagster UI

To see what you've built so far, you can load your project in the Dagster UI:

<CliInvocationExample contents="dg dev" />

To materialize assets and load tables in the DuckDB instance, click **Materialize All**:

![](/images/guides/build/projects-and-components/components/sling.png)

### 7. Verify the DuckDB tables

To verify the DuckDB tables were correctly populated, run the following command:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/16-duckdb-select.txt" />

## Transform data

To transform the data you downloaded in the previous section, you will need to download a sample dbt project from GitHub and use the data ingested with Sling as an input for the dbt project.

### 1. Clone the sample dbt project from GitHub

First, clone the sample dbt project and delete the embedded git repository:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/17-jaffle-clone.txt" />

:::note

In this tutorial, we have you clone the dbt project into your Dagster project. However, you can clone the dbt project anywhere as long as you set the relative path to the dbt project correctly in the dbt project `component.yaml`.

:::

### 2. Install the dbt project component type

To interface with the dbt project, you will need to instantiate a Dagster dbt project component. To make the dbt project component type available, install the dbt integrations `dagster-dbt` and `dbt-duckdb`:

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/18-uv-add-dbt.txt" />
  </TabItem>
  <TabItem value="pip" label="pip">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/18-pip-add-dbt.txt" />
  </TabItem>
</Tabs>

Confirm that the `dagster_dbt.DbtProjectComponent` component type is available by running `dg list plugins`:

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/19-dg-list-plugins.txt" />
</WideContent>

### 3. Scaffold a new instance of the dbt project component

Next, scaffold a new instance of the `dagster_dbt.DbtProjectComponent` component, providing the path to the dbt project you cloned earlier as the `project_path` scaffold parameter:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/20-dg-scaffold-jdbt.txt" />

This creates a new dbt project component instance at `jaffle_platform/defs/jdbt`. To see the component configuration, open `component.yaml` in that directory:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/21-component-jdbt.yaml"
  language="YAML"
  title="jaffle-platform/src/jaffle_platform/defs/jdbt/component.yaml"
/>

:::info

A bug in the component scaffolding for `DbtProjectComponent` is currently
causing the `project_dir` in `src/jaffle_platform/defs/jdbt/component.yaml` path to be generated as `../../../dbt/jdbt` when it should be `../../../../dbt/jdbt`. Please update the `project_dir` to `../../../../dbt/jdbt` before proceeding. This will be fixed in the next release.

:::

### 4. Update the dbt project component configuration

To see the new dbt assets in the Dagster UI, run `dg dev`:

<CliInvocationExample contents="dg dev" />

![DAG with dbt assets](/images/guides/build/projects-and-components/components/dbt-1.png)

You can see that there appear to be two copies of the `raw_customers`, `raw_orders`, and `raw_payments` tables. If you click on the new assets, you will see that the asset keys generated by the dbt project component contain `main/*`, whereas the keys generated by the Sling component contain `target/main/*`.

To fix this, you will need to update the dbt project component configuration to match the keys generated by the Sling component. Update `components/jdbt/component.yaml` with the configuration below:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/24-project-jdbt.yaml"
  language="YAML"
  title="jaffle-platform/src/jaffle_platform/defs/jdbt/component.yaml"
/>

To verify the fix, click **Reload definitions** in the Dagster UI:

![DAG with reloaded definitions](/images/guides/build/projects-and-components/components/dbt-2.png)

Now the asset keys generated by the Sling and dbt project components match, and the asset graph has the expected assets. To materialize the new assets defined by the dbt project component, click **Materialize All**.

To further verify the fix, you can view a sample of the newly materialized assets in DuckDB from the command line:

<WideContent maxSize={1000}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/26-duckdb-select-orders.txt" />
</WideContent>

## Visualize data

To visualize the data you've just transformed, you can use [Evidence.dev](https://www.evidence.dev/), an open-source BI tool.

### 1. Install the `dagster-evidence` package

First, install the `dagster-evidence` package with either `uv` or `pip`:

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/27-uv-add-evidence.txt" />
  </TabItem>
  <TabItem value="pip" label="pip">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/27-pip-add-evidence.txt" />
  </TabItem>
</Tabs>

Confirm that the `EvidenceProject` component type is available by running `dg list plugins`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/28-dg-list-plugins.txt" />

### 2. Clone the sample Evidence project from GitHub

Clone the example Evidence dashboard project and install the dependencies:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/29-jaffle-dashboard-clone.txt" />

```shell
cd jaffle_dashboard && npm install
```

:::note

In this tutorial, we have you clone the Evidence project into your Dagster project. However, you can clone the Evidence project anywhere as long as you set the relative path to the Evidence project correctly in the Evidence component `component.yaml`.

:::

### 3. Scaffold a new instance of the Evidence project component

Use the `dg scaffold` command to scaffold a new instance of the Evidence project component:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/30-scaffold-jaffle-dashboard.txt" />

This command will generate an empty YAML file:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/31-component-jaffle-dashboard.yaml"
  language="YAML"
  title="jaffle-platform/jaffle_platform/defs/jaffle_dashboard/component.yaml"
/>

### 4. Configure the Evidence project component

Next, update the Evidence project component configuration to target the `jaffle_dashboard` Evidence project, and connect it to the upstream `orders` and `customers` assets:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/32-project-jaffle-dashboard.yaml"
  language="YAML"
  title="jaffle-platform/jaffle_platform/defs/jaffle_dashboard/component.yaml"
/>

To verify that the YAML is correctly formatted, run `dg check yaml`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/33-dg-component-check-yaml.txt" />

To verify that the definitions load successfully, run `dg check defs`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/34-dg-component-check-defs.txt" />

### 5. Generate and view the Evidence dashboard

To generate a static website for your Evidence dashboard, materialize the `jaffle_dashboard` asset in the Dagster UI. The website will be created in the `jaffle_dashboard/build` directory.

To view the dashboard in your browser, run the following commands:

```bash
cd jaffle_dashboard/build && python -m http.server
```

You should see a dashboard like the following at `http://localhost:8000/`:

![](/images/guides/build/projects-and-components/components/evidence.png)

## Automate your pipeline

Now that you've defined some assets, you can automate them with a schedule.

Make sure you are in the `jaffle-platform` directory, then scaffold a schedule:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/35-scaffold-daily-jaffle.txt" />

Next, update the schedule to target all assets with `*`, and set `cron_schedule` to `@daily`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/36-daily-jaffle.py"
  language="Python"
  title="jaffle-platform/src/jaffle_platform/defs/daily_jaffle.py"
/>

Finally, verify the schedule was added to your Dagster project with `dg list defs`:

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/37-dg-list-defs.txt" />
</WideContent>

## Next steps

To continue your journey with components, you can [add more components to your project](/guides/labs/components/building-pipelines-with-components/adding-components) or learn how to [manage multiple components-ready projects with `dg`](/guides/labs/dg/multiple-projects).
