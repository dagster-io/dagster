---
title: Using resources in projects
sidebar_position: 250
description: Using resources in Dagster dg projects for entities such as assets, asset checks, and sensors.
---

import DgComponentsRc from '@site/docs/partials/\_DgComponentsRc.md';

<DgComponentsRc />

:::note Prerequisites

Before following this guide, you will need to [create a project](/guides/build/projects/creating-a-new-project) with the [`create-dagster` CLI](/api/clis/create-dagster).

:::

[Assets](/guides/build/assets), [asset checks](/guides/test/asset-checks), and [sensors](/guides/automate/sensors) in Dagster frequently require resources that are instantiated elsewhere in the project.

For example, if you have created a new Dagster project with `dg` called `my_project`, you can define the resources at `src/my_project/defs/aresource.py`:

<CodeExample path="docs_snippets/docs_snippets/guides/dg/using-resources/2-resources-at-defs-root.py" title="src/my_project/defs/aresource.py" />

You can then make that resource available anywhere else in your project by defining a <PyObject section="definitions" module="dagster" object="Definitions" decorator /> function:

<CodeExample path="docs_snippets/docs_snippets/guides/dg/using-resources/3-resource-defs-at-project-root.py" title="src/my_project/defs/resources.py" />

You can now use the resource elsewhere in your project:

<CodeExample path="docs_snippets/docs_snippets/guides/dg/using-resources/1-asset-one.py" title="src/my_project/defs/assets.py" />

## Scaffolding resources

To create a resource dictionary like the above, you can run the following:

```bash
dg scaffold defs dagster.resources resources.py
```

which will create:

<CodeExample path="docs_snippets/docs_snippets/guides/dg/using-resources/4-scaffolded-resource-defs.py" title="src/<project_name>/defs/resources.py" />

and you can fill out the resource dictionary as needed.
