---
title: Dagster & Airbyte (Component)
sidebar_position: 3
sidebar_label: Airbyte Cloud & OSS (Component)
description: The dagster-airbyte library provides an AirbyteWorkspaceComponent, which can be used to represent Airbyte connections as assets in Dagster.
tags: [dagster-supported, etl, component]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-airbyte
pypi: https://pypi.org/project/dagster-airbyte/
sidebar_custom_props:
  logo: images/integrations/airbyte.svg
partnerlink: https://airbyte.com/tutorials/orchestrate-data-ingestion-and-transformation-pipelines
---

The [dagster-airbyte](/integrations/libraries/airbyte/dagster-airbyte) library provides an `AirbyteWorkspaceComponent` which can be used to easily represent Airbyte connections as assets in Dagster.

:::info

`AirbyteWorkspaceComponent` is a [state-backed component](/guides/build/components/state-backed-components), which fetches and caches Airbyte workspace metadata. For information on managing component state, see [Configuring state-backed components](/guides/build/components/state-backed-components/configuring-state-backed-components).

:::

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-component/1-scaffold-project.txt" />

Activate the project virtual environment:

```
source ../.venv/bin/activate
```

Finally, add the `dagster-airbyte` library to the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-component/2-add-airbyte.txt" />

## 2. Scaffold an Airbyte component

Now that you have a Dagster project, you can scaffold an Airbyte component. You'll need to provide your Airbyte workspace ID and API credentials:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-component/3-scaffold-airbyte-component.txt" />

The scaffold call will generate a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-component/4-tree.txt" />

In its scaffolded form, the `defs.yaml` file contains the configuration for your Airbyte workspace:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-component/5-component.yaml"
  title="my_project/defs/airbyte_ingest/defs.yaml"
  language="yaml"
/>

You can check the configuration of your component:

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-component/6-list-defs.txt" />
</WideContent>

## 3. Configuration for Airbyte OSS or Self-Managed Enterprise

In order to configure your Airbyte component for Airbyte OSS or Self-Managed Enterprise, you will need to provide the [REST API URL](https://docs.airbyte.com/platform/api-documentation#using-the-airbyte-api) and [Configuration API URL](https://docs.airbyte.com/platform/api-documentation#configuration-api-deprecated).

The REST API URL endpoint is exposed at `https://<airbyte-server-hostname>/api/public/v1` and the Configuration API URL endpoint is exposed at `https://<airbyte-server-hostname>/api/v1`.

Airbyte OSS and Self-Managed Enterprise support several authentication methods. Please see [Authentication in Self-Managed](https://reference.airbyte.com/reference/authentication#authentication-in-self-managed-enterprise) in the Airbyte API docs for more details.

<Tabs persistentKey="airbyteauth">
<TabItem value="OAuth Client Credentials">

<CodeExample
  path="docs_snippets/docs_snippets/integrations/airbyte/component/7-oss-oauth-component.yaml"
  title="my_project/defs/airbyte_ingest/defs.yaml"
  language="yaml"
/>

</TabItem>
<TabItem value="Basic Authentication">

<CodeExample
  path="docs_snippets/docs_snippets/integrations/airbyte/component/8-oss-basic-auth-component.yaml"
  title="my_project/defs/airbyte_ingest/defs.yaml"
  language="yaml"
/>

</TabItem>
<TabItem value="No Authentication">

<CodeExample
  path="docs_snippets/docs_snippets/integrations/airbyte/component/9-oss-no-auth-component.yaml"
  title="my_project/defs/airbyte_ingest/defs.yaml"
  language="yaml"
/>

</TabItem>
</Tabs>

## 4. Select specific connections

You can select specific Airbyte connections to include in your component using the `connection_selector` key. This allows you to filter which connections are represented as assets:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-component/10-customized-component.yaml"
  title="my_project/defs/airbyte_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-component/11-list-defs.txt" />
</WideContent>

## 5. Customize Airbyte assets

Properties of the assets emitted by each connection can be customized in the `defs.yaml` file using the `translation` key:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-component/12-customized-component.yaml"
  title="my_project/defs/airbyte_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/airbyte-component/13-list-defs.txt" />
</WideContent>
