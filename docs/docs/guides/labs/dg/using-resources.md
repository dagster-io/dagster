---
title: Using resources in dg projects
sidebar_label: 'Using resources'
sidebar_position: 250
description: Using resources in Dagster dg projects for entities such as assets, asset checks, and sensors.
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

:::note Prerequisites

Before following this guide, you will need to [create a project](/guides/labs/dg/creating-a-project) with the `create-dagster` CLI.

:::

[Assets](/guides/build/assets),[asset checks](/guides/test/asset-checks), and [sensors](/guides/automate/sensors) in Dagster frequently require resources that are instantiated elsewhere in the project.

For example, if you have an asset:

<CodeExample path="docs_snippets/docs_snippets/guides/dg/using-resources/1-asset-one.py" />

And a separately defined resource at the root of the project:

<CodeExample path="docs_snippets/docs_snippets/guides/dg/using-resources/2-resources-at-defs-root.py" />

Resources can be added at any level in the `defs` hierarchy by creating a `Definitions` object.

<CodeExample path="docs_snippets/docs_snippets/guides/dg/using-resources/3-resource-defs-at-project-root.py" />

Resource binding can happen at any level of the hierarchy. Which means that if you moved `asset_one` in this example to be in a subdirectory, you could leave the existing `resources.py` file at `src/defs/resources.py`.

```
src
└── resource_docs
    ├── definitions.py
    ├── defs
    │   ├── assets
    │   │   └── asset_one.py # contains def asset_one():
    │   └── resources.py # contains AResource()
    └── resources.py # contains class AResource
```

We have a scaffold command that makes this straightforward.

You can run

```
dg scaffold defs dagster.resources path/to/resources.py
```

which will create

```
import dagster as dg

@dg.definitions
def resources() -> dg.Definitions:
    return dg.Definitions(resources={})
```

and you can fill out the resource dictionary as needed.
