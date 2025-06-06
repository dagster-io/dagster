---
title: Create sling connection
description: Connect to Sling to pull in data
sidebar_position: 10
---

<Tabs>
    <TabItem value="components" label="Components">
        ```bash
        dg scaffold defs 'dagster_sling.SlingReplicationCollectionComponent' ingest_files
        ```

        This adds a Sling component instance called ingest_files to the src/jaffle_platform/defs directory of your project:

        <CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial_components/src/etl_tutorial_components/defs/ingest_files/tree.txt" />

        A single file, `defs.yaml`, was created in the ingest_files directory. Every Dagster component has a `defs.yaml` file that specifies the component type and any parameters used to scaffold definitions from the component at runtime:

        <CodeExample
            path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial_components/src/etl_tutorial_components/defs/ingest_files/component.yaml"
            language="YAML"
            title="src/etl_tutorial_components/defs/ingest_files/component.yaml"
        />

        Currently, the parameters in your Sling component `defs.yaml` define a single `replication`, which is a Sling term that specifies how data should be replicated from a source to a target. The replication details are specified in a `replication.yaml` file that is read by Sling. You will create this file shortly:

        <CodeExample
            path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial_components/src/etl_tutorial_components/defs/ingest_files/replication.yaml"
            language="YAML"
            title="src/etl_tutorial_components/defs/ingest_files/replication.yaml"
        />

        :::note
        The `path` parameter for a replication is relative to the same folder containing component.yaml. This is a convention for components.
        :::

    </TabItem>
    <TabItem value="assets" label="Assets">
        ```bash
        dg scaffold defs 'dagster.assets' assets.py
        ```

        dddddfsfadfsafafafafafafaf

        <CodeExample
            path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial_components/src/etl_tutorial_components/defs/sling_assets.py"
            language="python"
            title="src/etl_tutorial_components/defs/sling_assets.py"
        />

        zfgasfdsafasfasdf

        <CodeExample
            path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial_components/_int/resources.py"
            language="python"
            startAfter="start_sling_resource"
            endBefore="end_sling_resource"
            title="src/etl_tutorial_components/defs/resources.py"
        />

    </TabItem>
</Tabs>



