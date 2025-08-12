---
title: Dagster & Power BI (Component)
sidebar_label: Power BI
description: The dagster-powerbi library provides a PowerBIWorkspaceComponent, which can be used to represent Power BI assets as assets in Dagster.
tags: [dagster-supported, bi]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-powerbi
pypi: https://pypi.org/project/dagster-powerbi
sidebar_custom_props:
  logo: images/integrations/powerbi.svg
partnerlink: https://learn.microsoft.com/en-us/power-bi/
canonicalUrl: '/integrations/libraries/powerbi'
slug: '/integrations/libraries/powerbi'
---

The [dagster-powerbi](/integrations/libraries/powerbi) library provides a `PowerBIWorkspaceComponent` which can be used to easily represent Power BI dashboards, reports, semantic models, and data sources as assets in Dagster.

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/powerbi-component/1-scaffold-project.txt" />

Activate the project virtual environment:

```
source ../.venv/bin/activate
```

Finally, add the `dagster-powerbi` library to the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/powerbi-component/2-add-powerbi.txt" />

## 2. Scaffold a Power BI component

Now that you have a Dagster project, you can scaffold a Power BI component:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/powerbi-component/3-scaffold-powerbi-component.txt" />

The scaffold call will generate a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/powerbi-component/4-tree.txt" />

## 3. Configure your Power BI workspace

Update the `defs.yaml` file with your workspace ID. You will also need to provide either an API access token or service principal credentials. For more information on how to create a service principal, see [Embed Power BI content with service principal and an application secret](https://learn.microsoft.com/en-us/power-bi/developer/embedded/embed-service-principal) in the Power BI documentation.

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/powerbi-component/6-populated-component.yaml"
  title="my_project/defs/powerbi_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/powerbi-component/7-list-defs.txt" />
</WideContent>

## 4. Enable semantic model refresh

You can enable refreshing semantic models by adding the `enable_semantic_model_refresh` key. To enable refresh for all semantic models, set the value to `True`.

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/powerbi-component/8-customized-component.yaml"
  title="my_project/defs/powerbi_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/powerbi-component/9-list-defs.txt" />
</WideContent>

To enable refreshing specific semantic models, set the value to a list of semantic model names:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/powerbi-component/10-customized-component.yaml"
  title="my_project/defs/powerbi_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/powerbi-component/11-list-defs.txt" />
</WideContent>

## 5. Customize Power BI asset metadata

You can customize the metadata and grouping of Power BI assets using the `translation` key:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/powerbi-component/12-customized-component.yaml"
  title="my_project/defs/powerbi_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/powerbi-component/13-list-defs.txt" />
</WideContent>

### Customize specific data types

You may also specify distinct translation behavior for specific data types. For example, you can add a tag to all semantic models:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/powerbi-component/14-customized-semantic-translation.yaml"
  title="my_project/defs/powerbi_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/powerbi-component/15-list-defs.txt" />
</WideContent>
