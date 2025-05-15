---
title: Setup
sidebar_position: 100
---

import AirliftPreview from '@site/docs/partials/\_AirliftPreview.md';

<AirliftPreview />

## Install `dg`

To install `dg`, follow the [`dg` installation guide](https://docs.dagster.io/guides/labs/dg).

## Create a components-ready project

To create a components-ready project, follow the [project creation guide](https://docs.dagster.io/guides/labs/dg/creating-a-project).

## Add the Airlift component to your project

Add the Airlift component type to your environment:

```
uv add dagster-airlift
```

Create a new instance of the Airlift component:

```
dg scaffold <AirliftComponentTypeName> airlift_migrate
```
{/* TODO replace above with name of Airlift component */}