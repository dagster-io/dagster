---
title: Dagster & Airbyte Cloud (Component)
sidebar_label: Airbyte Cloud (Component)
description: The dagster-airbyte library provides an AirbyteCloudWorkspaceComponent, which can be used to represent Airbyte Cloud connections as assets in Dagster.
tags: [dagster-supported, etl]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-airbyte
pypi: https://pypi.org/project/dagster-airbyte/
sidebar_custom_props:
  logo: images/integrations/airbyte.svg
partnerlink: https://airbyte.com/tutorials/orchestrate-data-ingestion-and-transformation-pipelines
---

The [dagster-airbyte](/api/libraries/dagster-airbyte) library provides an `AirbyteCloudWorkspaceComponent` which can be used to easily represent Airbyte Cloud connections as assets in Dagster.

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-cloud-component/1-scaffold-project.txt" />

Activate the project virtual environment:

```
source ../.venv/bin/activate
```

Finally, add the `dagster-airbyte` library to the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-cloud-component/2-add-airbyte.txt" />

## 2. Scaffold an Airbyte Cloud component

Now that you have a Dagster project, you can scaffold an Airbyte Cloud component. You'll need to provide your Airbyte Cloud workspace ID and API credentials:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-cloud-component/3-scaffold-airbyte-component.txt" />

The scaffold call will generate a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-cloud-component/4-tree.txt" />

In its scaffolded form, the `defs.yaml` file contains the configuration for your Airbyte Cloud workspace:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-cloud-component/5-component.yaml"
  title="my_project/defs/airbyte_ingest/defs.yaml"
  language="yaml"
/>

You can check the configuration of your component:

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-cloud-component/6-list-defs.txt" />
</WideContent>

## 3. Select specific connections

You can select specific Airbyte Cloud connections to include in your component using the `connection_selector` key. This allows you to filter which connections are represented as assets:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-cloud-component/7-customized-component.yaml"
  title="my_project/defs/airbyte_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-cloud-component/8-list-defs.txt" />
</WideContent>

## 4. Customize Airbyte Cloud assets

Properties of the assets emitted by each connection can be customized in the `defs.yaml` file using the `translation` key:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-cloud-component/9-customized-component.yaml"
  title="my_project/defs/airbyte_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-cloud-component/10-list-defs.txt" />
</WideContent>
