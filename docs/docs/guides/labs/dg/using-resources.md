---
title: Using resources in dg projects
sidebar_label: 'Using resources'
sidebar_position: 250
description: Using resources in Dagster dg projects for entities such as assets, asset checks, and sensors.
---

Assets, asset checks, and sensors in Dagster frequently require resources that are instantiated elsewhere in the project.

For example you have an asset:

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
