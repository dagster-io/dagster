---
title: 'Dagster & dlt with components'
description: The dagster-dlt library provides a DltLoadCollectionComponent, which can be used to represent a collection of dlt sources and pipelines as assets in Dagster.
sidebar_position: 400
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

The [dagster-dlt](/integrations/libraries/dlt) library provides a `DltLoadCollectionComponent` which can be used to easily represent a collection of dlt sources and pipelines as assets in Dagster.

## Preparing a Dagster project

To begin, you'll need a Dagster project. You can use an existing project [ready for components](/guides/labs/dg/incrementally-adopting-dg/migrating-project) or scaffold a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/1-scaffold-project.txt" />

Next, you will need to add the `dagster-dlt` library to the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/2-add-dlt.txt" />


## Scaffolding a dlt component

Now that you have a Dagster project, you can scaffold a dlt component. You may optionally provide the source and destination types, which will be used to automatically generate a set of sample loads:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/3-scaffold-dlt-component.txt" />

The scaffold call will generate a `defs.yaml` file and a `loads.py` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/4-tree.txt" />

The `loads.py` file contains a number of dlt sources and pipelines which are referenced by Dagster, but can also be run directly using dlt:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/5-loads.py" title="my_project/defs/github_snowflake_ingest/loads.py" language="python" />

Each of these sources and pipelines are referenced by a fully scoped Python identifier in the `defs.yaml` file, pairing them into a set of loads:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/6-defs.yaml" title="my_project/defs/github_snowflake_ingest/defs.yaml" language="yaml" />

You can list the assets produced by the various loads:

<WideContent maxSize={1100}>
<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/7-list-defs.txt" />
</WideContent>

## Customizing dlt assets

Properties of the assets emitted by each load can be customized in the `defs.yaml` file using the `translation` key:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/8-customized-defs.yaml" title="my_project/defs/github_snowflake_ingest/defs.yaml" language="yaml" />

<WideContent maxSize={1100}>
<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/9-list-defs.txt" />
</WideContent>

Both the `DltResource` and `Pipeline` objects are available in scope, and can be used for dynamic customization:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/10-customized-defs.yaml" title="my_project/defs/github_snowflake_ingest/defs.yaml" language="yaml" />
