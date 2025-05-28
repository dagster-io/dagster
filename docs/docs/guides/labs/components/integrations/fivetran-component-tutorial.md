---
title: 'Dagster & Fivetran with components'
description: The dagster-fivetran library provides a FivetranWorkspaceComponent, which can be used to represent Fivetran connectors as assets in Dagster.
sidebar_position: 200
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

The [dagster-fivetran](/integrations/libraries/fivetran) library provides a `FivetranWorkspaceComponent` which can be used to easily represent Fivetran connectors as assets in Dagster.

## Preparing a Dagster project

To begin, you'll need a Dagster project. You can use an existing project [ready for components](/guides/labs/dg/incrementally-adopting-dg/migrating-project) or scaffold a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/1-scaffold-project.txt" />

Next, you will need to add the `dagster-fivetran` library to the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/2-add-fivetran.txt" />

## Scaffolding a Fivetran component

Now that you have a Dagster project, you can scaffold a Fivetran component. You'll need to provide your Fivetran account ID and API credentials:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/3-scaffold-fivetran-component.txt" />

The scaffold call will generate a `component.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/4-tree.txt" />

In its scaffolded form, the `component.yaml` file contains the configuration for your Fivetran workspace:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/5-component.yaml" title="my_project/defs/fivetran_ingest/component.yaml" language="yaml" />

You can check the configuration of your component:

<WideContent maxSize={1100}>
<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/6-list-defs.txt" />
</WideContent>

## Selecting specific connectors

You can select specific Fivetran connectors to include in your component using the `connector_selector` key. This allows you to filter which connectors are represented as assets:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/7-customized-component.yaml" title="my_project/defs/fivetran_ingest/component.yaml" language="yaml" />

<WideContent maxSize={1100}>
<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/8-list-defs.txt" />
</WideContent>

## Customizing Fivetran assets

Properties of the assets emitted by each connector can be customized in the `component.yaml` file using the `translation` key:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/9-customized-component.yaml" title="my_project/defs/fivetran_ingest/component.yaml" language="yaml" />

<WideContent maxSize={1100}>
<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/10-list-defs.txt" />
</WideContent>
