---
title: Dagster & Omni (Component)
sidebar_label: Omni
sidebar_position: 1
description: The dagster-omni library provides an OmniComponent, which can be used to represent Omni documents as assets in Dagster.
tags: [dagster-supported, bi, component]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-omni
pypi: https://pypi.org/project/dagster-omni
sidebar_custom_props:
  logo: images/integrations/omni.svg
partnerlink: https://omni.co/
canonicalUrl: '/integrations/libraries/omni'
slug: '/integrations/libraries/omni'
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

The [dagster-omni](/integrations/libraries/omni) library provides an `OmniComponent` which can be used to easily represent Omni documents and queries as assets in Dagster.

:::info

`OmniComponent` is a [state-backed component](/guides/build/components/state-backed-components), which fetches and caches Omni workspace metadata. For information on managing component state, see [Configuring state-backed components](/guides/build/components/state-backed-components/configuring-state-backed-components).

:::

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/omni-component/1-scaffold-project.txt" />

Activate the project virtual environment:

```
source ../.venv/bin/activate
```

Finally, add the `dagster-omni` library to the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/omni-component/2-add-omni.txt" />

## 2. Scaffold an Omni component definition

Now that you have a Dagster project, you can scaffold an Omni component definition:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/omni-component/3-scaffold-omni-component.txt" />

The `dg scaffold defs` call will generate a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/omni-component/4-tree.txt" />

## 3. Configure your Omni workspace

Update the `defs.yaml` file with your Omni workspace connection details. You'll need to provide your Omni instance URL and API key. For more information on creating API credentials, see the [Omni API documentation](https://docs.omni.co/docs/api/introduction).

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/omni-component/6-populated-component.yaml"
  title="my_project/defs/omni_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/omni-component/7-list-defs.txt" />
</WideContent>

## 4. Customize Omni asset metadata

You can customize the metadata and grouping of Omni assets using the `translation` key:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/omni-component/8-customized-component.yaml"
  title="my_project/defs/omni_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/omni-component/9-list-defs.txt" />
</WideContent>
