---
title: Dagster & Looker (Component)
sidebar_label: Looker
description: The dagster-looker library provides a LookerInstanceComponent, which can be used to represent Looker assets as assets in Dagster.
tags: [dagster-supported, bi]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-looker
pypi: https://pypi.org/project/dagster-looker
sidebar_custom_props:
  logo: images/integrations/looker.svg
partnerlink: https://www.looker.com/
canonicalUrl: '/integrations/libraries/looker'
slug: '/integrations/libraries/looker'
---

The [dagster-looker](/integrations/libraries/looker) library provides a `LookerInstanceComponent` which can be used to easily represent Looker dashboards and explores as assets in Dagster.

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/looker-component/1-scaffold-project.txt" />

Activate the project virtual environment:

```
source ../.venv/bin/activate
```

Finally, add the `dagster-looker` library to the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/looker-component/2-add-looker.txt" />

## 2. Scaffold a Looker component definition

Now that you have a Dagster project, you can scaffold a Looker component definition:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/looker-component/3-scaffold-looker-component.txt" />

The `dg scaffold defs` call will generate a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/looker-component/4-tree.txt" />

## 3. Configure your Looker instance

Update the `defs.yaml` file with your Looker instance connection details. You'll need to provide your base URL, client ID, and client secret. For more information on creating API credentials, see the [Looker API documentation](https://cloud.google.com/looker/docs/api-auth).

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/looker-component/6-populated-component.yaml"
  title="my_project/defs/looker_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/looker-component/7-list-defs.txt" />
</WideContent>

## 4. Filter Looker content

You can filter which Looker dashboards and explores are loaded using the `looker_filter` key. For example, you can load only dashboards from specific folders and only explores used in those dashboards:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/looker-component/8-customized-component.yaml"
  title="my_project/defs/looker_ingest/defs.yaml"
  language="yaml"
/>

## 5. Customize Looker asset metadata

You can customize the metadata and grouping of Looker assets using the `translation` key:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/looker-component/9-customized-component.yaml"
  title="my_project/defs/looker_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/looker-component/10-list-defs.txt" />
</WideContent>

### Customize specific data types

You may also specify distinct translation behavior for specific data types. For example, you can add a tag to all dashboards:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/looker-component/11-customized-dashboard-translation.yaml"
  title="my_project/defs/looker_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/looker-component/12-list-defs.txt" />
</WideContent>
