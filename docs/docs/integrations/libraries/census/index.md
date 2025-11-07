---
title: Dagster & Census (Component)
sidebar_label: Census
description: The dagster-census library provides a CensusComponent, which can be used to represent Census syncs as assets in Dagster.
tags: [community-supported, etl]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-census
pypi: https://pypi.org/project/dagster-census/
sidebar_custom_props:
  logo: images/integrations/census.svg
  community: true
partnerlink: https://www.getcensus.com/
canonicalUrl: '/integrations/libraries/census'
slug: '/integrations/libraries/census'
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

The [`dagster-census` library](/api/libraries/dagster-census) provides a `CensusComponent` which can be used to easily represent Census syncs as assets in Dagster.

:::info

`CensusComponent` is a [state-backed component](/guides/build/components/state-backed-components), which fetches and caches Census workspace metadata. For information on managing component state, see [Configuring state-backed components](/guides/build/components/state-backed-components/configuring-state-backed-components).

:::

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/census-component/1-scaffold-project.txt" />

Activate the project virtual environment:

```
source ../.venv/bin/activate
```

Finally, add the `dagster-census` library to the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/census-component/2-add-census.txt" />

## 2. Scaffold a Census component definition

Now that you have a Dagster project, you can scaffold a Census component definition. You'll need to provide your Census API key, which you can set as an environment variable on the command line:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/census-component/3-scaffold-census-component.txt" />

The `dg scaffold defs` call will generate a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/census-component/4-tree.txt" />

### YAML configuration

In its scaffolded form, the `defs.yaml` file contains the configuration for your Census workspace:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/census-component/5-component.yaml"
  title="my_project/defs/census_ingest/defs.yaml"
  language="yaml"
/>

## 3. Check the component configuration

You can check the configuration of your component with `dg list defs`:

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/census-component/6-list-defs.txt" />
</WideContent>

## 4. Select specific syncs

You can select specific Census syncs to include in your component using the `sync_selector` key. This allows you to filter which syncs are represented as assets:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/census-component/7-customized-component.yaml"
  title="my_project/defs/census_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/census-component/8-list-defs.txt" />
</WideContent>

You can also select syncs by ID:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/census-component/9-customized-component-by-id.yaml"
  title="my_project/defs/census_ingest/defs.yaml"
  language="yaml"
/>

## About Census

**Census** syncs data from your cloud warehouse to the SaaS tools your organization uses. It allows everyone in your organization to take action with good data, no custom scripts or API integrations required.
