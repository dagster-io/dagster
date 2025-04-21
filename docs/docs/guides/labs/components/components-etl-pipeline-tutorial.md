---
title: 'Components ETL pipeline tutorial'
sidebar_position: 10
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';
import InstallUv from '@site/docs/partials/\_InstallUv.md';

<DgComponentsPreview />

## Setup

### 1. Install project dependencies

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

After installing dependencies, scaffold a components-ready project. The flow for scaffolding a project will depend on your package manager/environment management strategy.

<Tabs groupId="package-manager">
    <TabItem value="uv" label="uv">
        :::note Install uv
        <InstallUv />
        :::

        Ensure you have `dg` [installed globally](/guides/labs/dg) as a `uv` tool:

        <CliInvocationExample contents="uv tool install dagster-dg" />

        Now run the below command. Say yes to the prompt to run `uv sync` after scaffolding:

        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-a-uv-scaffold.txt" />

        The `dg init` command builds a project at `jaffle-platform`. Running `uv sync` after scaffolding creates a virtual environment and installs the dependencies listed in `pyproject.toml`, along with `jaffle-platform` itself as an [editable install](https://setuptools.pypa.io/en/latest/userguide/development_mode.html). Now let's enter the directory and activate the virtual environment:

        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-b-uv-scaffold.txt" />
    </TabItem>
    <TabItem value="pip" label="pip">
        Because `pip` does not support global installations, you will install `dg` inside your project virtual environment.
        We'll create and enter our project directory, initialize and activate a virtual environment, and install the `dagster-dg` package into it:
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-a-pip-scaffold.txt" />
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-b-pip-scaffold.txt" />
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-c-pip-scaffold.txt" />
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-d-pip-scaffold.txt" />
        The `dg` executable is now available via the activated virtual environment. Let's run `dg init .` to scaffold a new project. The `.` tells `dg` to scaffold the project in the current directory.
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-e-pip-scaffold.txt" />
        Finally, install the newly created project package into the virtual environment as an [editable install](https://setuptools.pypa.io/en/latest/userguide/development_mode.html):
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-f-pip-scaffold.txt" />
    </TabItem>

</Tabs>

To learn more about the files, directories, and default settings in a project scaffolded with `dg init`, see "[Creating a project with components](/guides/labs/components/building-pipelines-with-components/creating-a-project-with-components#project-structure)".

## Ingest data

### 1. Add the Sling component type to your environment

To ingest data, you must set up [Sling](https://slingdata.io/). We can list the component types available to our project with `dg list plugins`. If we run this now, the Sling component won't appear, since the `dagster` package doesn't contain components for specific integrations (like Sling):

<WideContent maxSize={1300}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/7-dg-list-plugins.txt" />
</WideContent>

To make the Sling component available in your environment, install the `dagster-sling` package:

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/8-uv-add-sling.txt" />
  </TabItem>
  <TabItem value="pip" label="pip">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/8-pip-add-sling.txt" />
  </TabItem>
</Tabs>

### 2. Confirm availability of the Sling component type

To confirm that the `dagster_sling.SlingReplicationCollectionComponent` component type is now available, run the `dg list plugins` command again:

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/9-dg-list-plugins.txt" />
</WideContent>

### 3. Create a new instance of the Sling component

Next, create a new instance of this component type:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/10-dg-scaffold-sling-replication.txt" />

This adds a component instance to the project at `jaffle_platform/defs/ingest_files`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/11-tree-jaffle-platform.txt" />

A single file, `component.yaml`, was created in the component folder. The `component.yaml` file is common to all Dagster components, and specifies the component type and any parameters used to scaffold definitions from the component at runtime.

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/12-component.yaml"
  language="YAML"
  title="jaffle-platform/src/jaffle_platform/defs/ingest_files/component.yaml"
/>

Right now the parameters define a single "replication"-- this is a Sling concept that specifies how data should be replicated from a source to a target. The details are specified in a `replication.yaml` file that is read by Sling. This file does not yet exist-- we are going to create it shortly.

:::note
The `path` parameter for a replication is relative to the same folder containing component.yaml. This is a convention for components.
:::

### 4. Download files for Sling source

Next, you will need to download some files locally to use your Sling source, since Sling doesn't support reading from the public internet:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/13-curl.txt" />

### 5. Set up the Sling to DuckDB replication

Create a `replication.yaml` file that references the downloaded files:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/14-replication.yaml"
  language="YAML"
  title="jaffle-platform/src/jaffle_platform/defs/ingest_files/replication.yaml"
/>

Finally, modify the `component.yaml` file to tell the Sling component where replicated data with the `DUCKDB` target should be written:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/15-component-connections.yaml"
  language="YAML"
  title="jaffle-platform/src/jaffle_platform/defs/ingest_files/component.yaml"
/>

### 6. View and materialize assets in the Dagster UI

Load your project in the Dagster UI to see what you've built so far. To materialize assets and load tables in the DuckDB instance, click **Materialize All**:

<CliInvocationExample contents="dg dev" />

![](/images/guides/build/projects-and-components/components/sling.png)

Verify the DuckDB tables on the command line:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/16-duckdb-select.txt" />

## Transform data

To transform the data, you will need to download a sample dbt project from GitHub and use the data ingested with Sling as an input for the dbt project.

### 1. Clone a sample dbt project from GitHub

First, clone the project and delete the embedded git repo:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/17-jaffle-clone.txt" />

### 2. Install the dbt project component type

To interface with the dbt project, you will need to instantiate a Dagster dbt project component. To access the dbt project component type, install the dbt integration `dagster-dbt` and `dbt-duckdb`:

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/18-uv-add-dbt.txt" />
  </TabItem>
  <TabItem value="pip" label="pip">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/18-pip-add-dbt.txt" />
  </TabItem>
</Tabs>

To confirm that the `dagster_dbt.DbtProjectComponent` component type is now available, run `dg list plugins`:

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/19-dg-list-plugins.txt" />
</WideContent>

### 3. Scaffold a new instance of the dbt project component

Next, scaffold a new instance of the `dagster_dbt.DbtProjectComponent` component, providing the path to the dbt project you cloned earlier as the `project_path` scaffold parameter:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/20-dg-scaffold-jdbt.txt" />

This creates a new component instance in the project at `jaffle_platform/defs/jdbt`. To see the component configuration, open `component.yaml` in that directory:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/21-component-jdbt.yaml"
  language="YAML"
  title="jaffle-platform/src/jaffle_platform/defs/jdbt/component.yaml"
/>

### 4. Update the dbt project component configuration

:::note
A bug in the component scaffolding for `DbtProjectComponent` is currently
causing the `project_dir` in `jaffle_platform/defs/dbt/component.yaml` path to be generated as `../../../dbt/jdbt` when it should be `../../../../dbt/jdbt`. Please update the `project_dir` to `../../../../dbt/jdbt` before proceeding. This will be fixed in the next release.
:::

Let’s see the project in the Dagster UI:

<CliInvocationExample contents="dg dev" />

![](/images/guides/build/projects-and-components/components/dbt-1.png)

You can see that there appear to be two copies of the `raw_customers`, `raw_orders`, and `raw_payments` tables. If you click on the assets, you can see their full asset keys. The keys generated by the dbt component are of the form `main/*`, whereas the keys generated by the Sling component are of the form `target/main/*`.

We need to update the configuration of the `dagster_dbt.DbtProjectComponent` component to match the keys generated by the Sling component. Update `components/jdbt/component.yaml` with the configuration below:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/22-project-jdbt-incorrect.yaml"
  language="YAML"
  title="jaffle-platform/src/jaffle_platform/defs/jdbt/component.yaml"
/>

You might notice the typo in the above file--after updating a component file, it's useful to validate that the changes match the component's schema. You can do this by running `dg check yaml`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/23-dg-component-check-error.txt" />

You can see that the error message includes the filename, line number, and a code snippet showing the exact nature of the error. Let's fix the typo:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/24-project-jdbt.yaml"
  language="YAML"
  title="jaffle-platform/src/jaffle_platform/defs/jdbt/component.yaml"
/>

Finally, run `dg check yaml` again to validate the fix:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/25-dg-component-check.txt" />

Reload the project in Dagster UI to verify that the keys load properly:

![](/images/guides/build/projects-and-components/components/dbt-2.png)

Now the keys generated by the Sling and dbt project components match, and the asset graph is correct. To materialize the new assets defined via the dbt project component, click **Materialize All**.

To verify the fix, you can view a sample of the newly materialized assets in DuckDB from the command line:

<WideContent maxSize={1000}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/26-duckdb-select-orders.txt" />
</WideContent>

## Visualize data

To visualize the data we've just transformed we'll use [Evidence.dev](https://www.evidence.dev/), an open-source BI tool.

### 1. Install the `dagster-evidence` package

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/27-uv-add-evidence.txt" />
  </TabItem>
  <TabItem value="pip" label="pip">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/27-pip-add-evidence.txt" />
  </TabItem>
</Tabs>

You will see that the `dagster-evidence` package provides a new `EvidenceProject` component type:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/28-dg-list-plugins.txt" />

### 2. Clone a sample Evidence project from GitHub

Clone the example dashboard project, and install the dependencies with:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/29-jaffle-dashboard-clone.txt" />

```shell
cd jaffle_dashboard && npm install
```

### 3. Scaffold a new instance of the Evidence project component

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/30-scaffold-jaffle-dashboard.txt" />

It will generate an empty YAML file:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/31-component-jaffle-dashboard.yaml"
  language="YAML"
  title="jaffle-platform/jaffle_platform/defs/jaffle_dashboard/component.yaml"
/>

### 4. Configure the component

Let's update the configuration of the component to target the `jaffle_dashboard` Evidence project, and wire it up to our two upstream assets:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/32-project-jaffle-dashboard.yaml"
  language="YAML"
  title="jaffle-platform/jaffle_platform/defs/jaffle_dashboard/component.yaml"
/>

And let's verify that the YAML is correct:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/33-dg-component-check-yaml.txt" />

And that the definitions load successfully:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/34-dg-component-check-defs.txt" />

Next, materialize the `jaffle_dashboard` asset, and it will generate a static website for your dashboard in the `jaffle_dashboard/build` directory.

You can view the dashboard in your browser by running `python -m http.server` in that folder, which will show a dashboard like this!

![](/images/guides/build/projects-and-components/components/evidence.png)

## Automate the pipeline

Now that you've defined some assets, let's schedule them.

First scaffold in a schedule:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/35-scaffold-daily-jaffle.txt" />

And now target `*` and schedule `@daily`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/36-daily-jaffle.py"
  language="Python"
  title="jaffle-platform/src/jaffle_platform/defs/daily_jaffle.py"
/>

## Next steps

To continue your journey with components, you can [add more components to your project](/guides/labs/components/building-pipelines-with-components/adding-components) or learn how to [manage multiple components-ready projects with `dg`](/guides/labs/dg/multiple-projects).
