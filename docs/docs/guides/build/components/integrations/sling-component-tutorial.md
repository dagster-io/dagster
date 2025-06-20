---
title: 'Dagster & Sling with components'
description: The dagster-sling library provides a SlingReplicationCollectionComponent, which can be used to represent a collection of Sling replications as assets in Dagster.
sidebar_position: 200
---

import DgComponentsRc from '@site/docs/partials/_DgComponentsRc.md';

<DgComponentsRc />

The [dagster-sling](/integrations/libraries/sling) library provides a `SlingReplicationCollectionComponent` which can be used to easily represent a collection of [Sling](https://slingdata.io/) replications as assets in Dagster.

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/1-scaffold-project.txt" />

Activate the project virtual environment:

<CliInvocationExample contents="source ../.venv/bin/activate" />

Finally, add the `dagster-sling` library to the project. We will also add `duckdb` to use as a destination for our Sling replication.

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/2-add-sling.txt" />

## 2. Scaffold a Sling component

Now that you have a Dagster project, you can scaffold a Sling component:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/3-scaffold-sling-component.txt" />

The scaffold call will generate a `defs.yaml` file and a unpopulated Sling `replication.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/4-tree.txt" />

In its scaffolded form, the `defs.yaml` file contains the configuration for your Sling workspace:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/5-component.yaml" title="my_project/defs/sling_ingest/defs.yaml" language="yaml" />

The generated file is a template, which still needs to be configured:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/6-replication.yaml" title="my_project/defs/sling_ingest/replication.yaml" language="yaml" />

## 3. Configure Sling replications

In the `defs.yaml` file, you can directly specify a list of Sling [connections](https://docs.slingdata.io/sling-platform/platform/connections) which you can use in your replications. Here, you can specify a connection to DuckDB:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/9-customized-component.yaml" title="my_project/defs/sling_ingest/defs.yaml" language="yaml" />

For this example replication, we will ingest a set of CSV files to DuckDB. You can use `curl` to download some sample data:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/7-curl.txt" />

Next, you can configure Sling replications for each CSV file in `replication.yaml`:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/8-replication.yaml" title="my_project/defs/sling_ingest/replication.yaml" language="yaml" />

Our newly configured Sling component will produce an asset for each replicated file:

<WideContent maxSize={1100}>
<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/10-list-defs.txt" />
</WideContent>

## 4. Customize Sling assets

Properties of the assets emitted by each replication can be customized in the `defs.yaml` file using the `translation` key:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/11-customized-component.yaml" title="my_project/defs/sling_ingest/defs.yaml" language="yaml" />

<WideContent maxSize={1100}>
<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/12-list-defs.txt" />
</WideContent>
