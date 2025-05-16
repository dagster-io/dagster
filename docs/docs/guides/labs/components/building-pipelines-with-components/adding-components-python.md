---
description: Add Dagster components to your projects with Python using the dg scaffold command.
sidebar_position: 300
title: Adding components to your project with Python
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

In some cases, you may want to add a component to your project with Python rather than YAML.

## Prerequisites

Before adding a component with Python, you will need to either [create a components-compatible project with `dg`](/guides/labs/dg/creating-a-project) or [migrate an existing project to `dg`](/guides/labs/dg/incrementally-adopting-dg/migrating-project).

Additionally, to run the example below, you will need to clone the sample dbt project and delete the embedded git repository:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/17-jaffle-clone.txt" />

Then install the dbt project component:

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/18-uv-add-dbt.txt" />
  </TabItem>
  <TabItem value="pip" label="pip">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/18-pip-add-dbt.txt" />
  </TabItem>
</Tabs>

## Steps

To add a component with Python, you can use the `dg scaffold` command with the `--format python` option. For example, to scaffold the dbt project component, you can run the following:

```python
dg scaffold dagster_dbt.DbtProjectComponent jdbt --project-path dbt/jdbt --format python
```

Running this command will generate a `component.py` file, rather than a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/python-components/tree.txt" />