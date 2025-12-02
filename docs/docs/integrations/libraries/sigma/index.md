---
title: Dagster & Sigma (Component)
sidebar_label: Sigma
description: The dagster-sigma library provides a SigmaComponent, which can be used to represent Sigma assets as assets in Dagster.
tags: [dagster-supported, bi, component]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-sigma
pypi: https://pypi.org/project/dagster-sigma
sidebar_custom_props:
  logo: images/integrations/sigma.svg
partnerlink: https://www.sigmacomputing.com/
canonicalUrl: '/integrations/libraries/sigma'
slug: '/integrations/libraries/sigma'
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

The [dagster-sigma](/integrations/libraries/sigma) library provides a `SigmaComponent` which can be used to easily represent Sigma workbooks and datasets as assets in Dagster.

:::info

`SigmaComponent` is a [state-backed component](/guides/build/components/state-backed-components), which fetches and caches Sigma organization metadata. For information on managing component state, see [Configuring state-backed components](/guides/build/components/state-backed-components/configuring-state-backed-components).

:::

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sigma-component/1-scaffold-project.txt" />

Activate the project virtual environment:

```
source ../.venv/bin/activate
```

Finally, add the `dagster-sigma` library to the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sigma-component/2-add-sigma.txt" />

## 2. Scaffold a Sigma component definition

Now that you have a Dagster project, you can scaffold a Sigma component definition:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sigma-component/3-scaffold-sigma-component.txt" />

The `dg scaffold defs` call will generate a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sigma-component/4-tree.txt" />

## 3. Configure your Sigma organization

Update the `defs.yaml` file with your Sigma organization connection details. You'll need to provide your base URL, client ID, and client secret. For more information on creating API credentials, see the [Sigma API documentation](https://help.sigmacomputing.com/reference/get-started-sigma-api).

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/sigma-component/6-populated-component.yaml"
  title="my_project/defs/sigma_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sigma-component/7-list-defs.txt" />
</WideContent>

## 4. Filter Sigma content

You can filter which Sigma workbooks and datasets are loaded using the `sigma_filter` key. For example, you can load only workbooks from specific folders and exclude unused datasets:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/sigma-component/8-customized-component.yaml"
  title="my_project/defs/sigma_ingest/defs.yaml"
  language="yaml"
/>

## 5. Customize Sigma asset metadata

You can customize the metadata and grouping of Sigma assets using the `translation` key:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/sigma-component/9-customized-component.yaml"
  title="my_project/defs/sigma_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sigma-component/10-list-defs.txt" />
</WideContent>

### Customize specific data types

You may also specify distinct translation behavior for specific data types. For example, you can add a tag to all workbooks:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/sigma-component/11-customized-workbook-translation.yaml"
  title="my_project/defs/sigma_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/sigma-component/12-list-defs.txt" />
</WideContent>
