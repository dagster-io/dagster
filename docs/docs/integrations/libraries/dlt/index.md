---
title: Dagster & dlt (Component)
sidebar_label: dlt
sidebar_position: 1
description: The dagster-dlt library provides a DltLoadCollectionComponent, which can be used to represent a collection of dlt sources and pipelines as assets in Dagster.
tags: [dagster-supported, etl, component]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dlt
pypi: https://pypi.org/project/dagster-dlt/
sidebar_custom_props:
  logo: images/integrations/dlthub.jpeg
partnerlink: https://dlthub.com/
canonicalUrl: '/integrations/libraries/dlt'
slug: '/integrations/libraries/dlt'
---

The [dagster-dlt](/integrations/libraries/dlt/dagster-dlt) library provides a `DltLoadCollectionComponent` which can be used to easily represent a collection of dlt sources and pipelines as assets in Dagster.

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/1-scaffold-project.txt" />

Activate the project virtual environment:

```
source ../.venv/bin/activate
```

Finally, add the `dagster-dlt` library to the project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/2-add-dlt.txt" />

## 2. Scaffold a dlt component definition

Now that you have a Dagster project, you can scaffold a dlt component definition. You may optionally provide the source and destination types, which will pull in the appropriate dlt source:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/3-scaffold-dlt-component.txt" />

The `dg scaffold defs` call will generate a basic `defs.yaml` file and a `loads.py` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/4-tree.txt" />

The `loads.py` file contains a skeleton dlt source and pipeline which are referenced by Dagster, but can also be run directly using dlt:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/5-loads.py"
  title="my_project/defs/github_snowflake_ingest/loads.py"
  language="python"
/>

Each of these sources and pipelines are referenced by a fully scoped Python identifier in the `defs.yaml` file, pairing them into a set of loads:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/6-defs.yaml"
  title="my_project/defs/github_snowflake_ingest/defs.yaml"
  language="yaml"
/>

## 3. Configure dlt loads

Next, you can fill in the template `loads.py` file with your own dlt sources and pipelines:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/7-customized-loads.py"
  title="my_project/defs/github_snowflake_ingest/loads.py"
  language="python"
/>

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/8-customized-defs.yaml"
  title="my_project/defs/github_snowflake_ingest/defs.yaml"
  language="yaml"
/>

You can use `dg list defs` to list the assets produced by the load:

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/9-list-defs.txt" />
</WideContent>

## 4. Customize Dagster assets

Properties of the assets emitted by each load can be customized in the `defs.yaml` file using the `translation` key:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/10-customized-defs.yaml"
  title="my_project/defs/github_snowflake_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/11-list-defs.txt" />
</WideContent>

Both the `DltResource` and `Pipeline` objects are available in scope, and can be used for dynamic customization:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dlt-component/12-customized-defs.yaml"
  title="my_project/defs/github_snowflake_ingest/defs.yaml"
  language="yaml"
/>
