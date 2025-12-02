---
title: Dagster & Fivetran (Component)
sidebar_label: Fivetran
description: The dagster-fivetran library provides a FivetranAccountComponent, which can be used to represent Fivetran connectors as assets in Dagster.
tags: [dagster-supported, etl, component]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-fivetran
pypi: https://pypi.org/project/dagster-fivetran/
sidebar_custom_props:
  logo: images/integrations/fivetran.svg
partnerlink: https://www.fivetran.com/
canonicalUrl: '/integrations/libraries/fivetran'
slug: '/integrations/libraries/fivetran'
---

The [`dagster-fivetran` library](/api/libraries/dagster-fivetran) provides a `FivetranAccountComponent` which can be used to easily represent Fivetran connectors as assets in Dagster.

:::info

`FivetranAccountComponent` is a [state-backed component](/guides/build/components/state-backed-components), which fetches and caches Fivetran workspace metadata. For information on managing component state, see [Configuring state-backed components](/guides/build/components/state-backed-components/configuring-state-backed-components).

:::

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/1-scaffold-project.txt" />

Activate the project virtual environment:

```
source ../.venv/bin/activate
```

Finally, add the `dagster-fivetran` library to the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/2-add-fivetran.txt" />

## 2. Scaffold a Fivetran component definition

Now that you have a Dagster project, you can scaffold a Fivetran component definition. You'll need to provide your Fivetran account ID and API credentials, which you can set as environment variables on the command line:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/3-scaffold-fivetran-component.txt" />

The `dg scaffold defs` call will generate a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/4-tree.txt" />

### YAML configuration

In its scaffolded form, the `defs.yaml` file contains the configuration for your Fivetran workspace:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/5-component.yaml"
  title="my_project/defs/fivetran_ingest/defs.yaml"
  language="yaml"
/>

## 3. Check the component configuration

You can check the configuration of your component with `dg list defs`:

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/6-list-defs.txt" />
</WideContent>

## 4. Select specific connectors

You can select specific Fivetran connectors to include in your component using the `connector_selector` key. This allows you to filter which connectors are represented as assets:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/7-customized-component.yaml"
  title="my_project/defs/fivetran_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/8-list-defs.txt" />
</WideContent>

## 5. Customize Fivetran assets

Properties of the assets emitted by each connector can be customized in the `defs.yaml` file using the `translation` key:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/9-customized-component.yaml"
  title="my_project/defs/fivetran_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/10-list-defs.txt" />
</WideContent>
