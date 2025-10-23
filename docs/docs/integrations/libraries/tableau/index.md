---
title: Dagster & Tableau (Component)
sidebar_label: Tableau
description: The dagster-tableau library provides a TableauComponent, which can be used to represent Tableau assets as assets in Dagster.
tags: [dagster-supported, bi]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-tableau
pypi: https://pypi.org/project/dagster-tableau
sidebar_custom_props:
  logo: images/integrations/tableau.svg
partnerlink: https://www.tableau.com/
canonicalUrl: '/integrations/libraries/tableau'
slug: '/integrations/libraries/tableau'
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

The [dagster-tableau](/integrations/libraries/tableau) library provides a `TableauComponent` which can be used to easily represent Tableau workbooks, sheets, dashboards, and data sources as assets in Dagster.

:::info

`TableauComponent` is a [state-backed component](/guides/build/components/state-backed-components), which fetches and caches Tableau workspace metadata. For information on managing component state, see [Configuring state-backed components](/guides/build/components/state-backed-components/configuring-state-backed-components).

:::

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/tableau-component/1-scaffold-project.txt" />

Activate the project virtual environment:

```
source ../.venv/bin/activate
```

Finally, add the `dagster-tableau` library to the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/tableau-component/2-add-tableau.txt" />

## 2. Scaffold a Tableau component definition

Now that you have a Dagster project, you can scaffold a Tableau component definition:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/tableau-component/3-scaffold-tableau-component.txt" />

The `dg scaffold defs` call will generate a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/tableau-component/4-tree.txt" />

## 3. Configure your Tableau workspace

Update the `defs.yaml` file with your Tableau workspace connection details. You'll need to provide your connected app credentials and site information. For more information on creating a connected app, see the [Tableau documentation](https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_concepts_auth.htm#connected-app).

The configuration depends on whether you're using Tableau Cloud or Tableau Server:

<Tabs>
<TabItem value="Using Dagster with Tableau Cloud">

For Tableau Cloud, set `type: cloud` and provide your `pod_name`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/tableau-component/6-populated-component.yaml"
  title="my_project/defs/tableau_ingest/defs.yaml"
  language="yaml"
/>

</TabItem>
<TabItem value="Using Dagster with Tableau Server">

For Tableau Server, set `type: server` and provide your `server_name` instead of `pod_name`:

```yaml
type: dagster_tableau.TableauComponent

attributes:
  workspace:
    type: server
    connected_app_client_id: '{{ env.TABLEAU_CLIENT_ID }}'
    connected_app_secret_id: '{{ env.TABLEAU_SECRET_ID }}'
    connected_app_secret_value: '{{ env.TABLEAU_SECRET_VALUE }}'
    username: '{{ env.TABLEAU_USERNAME }}'
    site_name: my_site
    server_name: tableau.example.com
```

</TabItem>
</Tabs>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/tableau-component/7-list-defs.txt" />
</WideContent>

## 4. Customize Tableau asset metadata

You can customize the metadata and grouping of Tableau assets using the `translation` key:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/tableau-component/8-customized-component.yaml"
  title="my_project/defs/tableau_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/tableau-component/9-list-defs.txt" />
</WideContent>

### Customize specific data types

You may also specify distinct translation behavior for specific data types. For example, you can add a tag to all sheets:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/tableau-component/10-customized-sheet-translation.yaml"
  title="my_project/defs/tableau_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/tableau-component/11-list-defs.txt" />
</WideContent>
