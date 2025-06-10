---
title: 'Dagster & Sling with components'
description: The dagster-sling library provides a SlingReplicationCollectionComponent, which can be used to represent a collection of Sling replications as assets in Dagster.
sidebar_position: 200
---

import DgComponentsPreview from '@site/docs/partials/_DgComponentsPreview.md';

<DgComponentsPreview />

The [dagster-sling](/integrations/libraries/sling) library provides a `SlingReplicationCollectionComponent` which can be used to easily represent a collection of Sling replications as assets in Dagster.

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/labs/dg/incrementally-adopting-dg/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/1-scaffold-project.txt" />

Activate the project virtual environment:

```
source ../.venv/bin/activate
```

Finally, add the `dagster-sling` library to the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/2-add-sling.txt" />

## 2. Scaffold a Sling component

Now that you have a Dagster project, you can scaffold a Sling component:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/3-scaffold-sling-component.txt" />

The scaffold call will generate a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/4-tree.txt" />

In its scaffolded form, the `defs.yaml` file contains the configuration for your Sling workspace:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/5-component.yaml" title="my_project/defs/sling_ingest/defs.yaml" language="yaml" />

You can check the configuration of your component:

<WideContent maxSize={1100}>
<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/7-list-defs.txt" />
</WideContent>

## 3. Configure Sling replications

You can configure the replications for your Sling component by editing the `replication.yaml` file:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/7-replication.yaml" title="my_project/defs/sling_ingest/replication.yaml" language="yaml" />

You can also customize the connections in your `defs.yaml` file:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/6-customized-component.yaml" title="my_project/defs/sling_ingest/defs.yaml" language="yaml" />

<WideContent maxSize={1100}>
<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/9-list-defs.txt" />
</WideContent>

## 4. Customize Sling assets

Properties of the assets emitted by each replication can be customized in the `defs.yaml` file using the `translation` key:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/8-customized-component.yaml" title="my_project/defs/sling_ingest/defs.yaml" language="yaml" />

<WideContent maxSize={1100}>
<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sling-component/11-list-defs.txt" />
</WideContent>
