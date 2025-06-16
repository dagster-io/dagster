---
title: Create Sling connection
description: Connect to Sling to pull in data
sidebar_position: 10
---

In the first step of the tutorial, you will use [Sling](https://slingdata.io/) to load files into [DuckDB](https://duckdb.org/). This data will serve as the foundation for the rest of the ETL tutorial.

- Integrate with Sling
- Build software-defined assets from a Sling project

:::note

You can set up this part of the Dagster project using either components or assets that you define yourself. Both options will provide you with the same functionality in Dagster. You can use components and assets together so choose whichever option you prefer for each section.

:::

<Tabs>
    <TabItem value="components" label="Components">
        
        **1. Define the Sling Component**

        ```bash
        dg scaffold defs 'dagster_sling.SlingReplicationCollectionComponent' ingest_files
        ```

        :::note

        The Sling component was added when you `uv pip install` the dependency at the beginning of this tutorial

        :::

        This adds a Sling component instance called `ingest_files` to the `src/jaffle_platform/defs` directory of your project:

        <CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial_components/src/etl_tutorial_components/defs/ingest_files/tree.txt" />

        **2. Define the Sling replication instance**

        A single file, `defs.yaml`, was created in the `ingest_files` directory. Every Dagster component has a `defs.yaml` file that specifies the component type and any parameters used to scaffold definitions from the component at runtime:

        <CodeExample
            path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial_components/src/etl_tutorial_components/defs/ingest_files/component.yaml"
            language="YAML"
            title="src/etl_tutorial_components/defs/ingest_files/component.yaml"
        />

        **3. Define teh Sling replication instance**

        Currently, the parameters in your Sling component `defs.yaml` define a single `replication`, which is a Sling term that specifies how data should be replicated from a source to a target. The replication details are specified in a `replication.yaml` file that is read by Sling. You will create this file shortly:

        <CodeExample
            path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial_components/src/etl_tutorial_components/defs/ingest_files/replication.yaml"
            language="YAML"
            title="src/etl_tutorial_components/defs/ingest_files/replication.yaml"
        />

    </TabItem>
    <TabItem value="assets" label="Assets">

        **1. Scaffold the assets**

        First you need to scaffold a file for the assets. This can be done using the `dg` cli.

        ```bash
        dg scaffold defs dagster.asset assets.py
        ```

        **2. Define the asset code**

        dddddfsfadfsafafafafafafaf

        <CodeExample
            path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial_components/src/etl_tutorial_components/defs/sling_assets.py"
            language="python"
            title="src/etl_tutorial_components/defs/sling_assets.py"
        />

        zfgasfdsafasfasdf

       **3. Scaffold the resources**

        Next we can define the resource that our assets rely on. Again we can use `dg` to scaffold our resources files and ensure it is in the correction location.

        ```bash
        dg scaffold defs dagster.resource resource.py
        ```

        **4. Define the resource code**

        <CodeExample
            path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial_components/_int/resources.py"
            language="python"
            startAfter="start_sling_resource"
            endBefore="end_sling_resource"
            title="src/etl_tutorial_components/defs/resources.py"
        />

    </TabItem>
</Tabs>

## Next steps

- Continue this tutorial with your [dbt](/etl-pipeline-tutorial/create-dbt-connection)
