---
title: 'Adding Dagster definitions to a dg project'
description: Dagster dg can be used to scaffold Dagster definitions such as assets, schedules, and sensors.
sidebar_label: 'Adding Dagster definitions'
sidebar_position: 200
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';
import DgScaffoldDefsTip from '@site/docs/partials/\_DgScaffoldDefsTip.md';

<DgComponentsPreview />

You can use the [`dg` CLI](/api/dagster/dg-cli) to scaffold Dagster definitions such as [assets](/guides/build/assets), [schedules](/guides/automate/schedules), and [sensors](/guides/automate/sensors).

:::note

All definitions added underneath the `defs` directory of a project created with the `create-dagster` CLI will be automatically loaded into the top-level `Definitions` object.

:::

## Prerequisites

Before scaffolding definitions with `dg`, you must [create a project](/guides/labs/dg/creating-a-project) with the `create-dagster CLI` and activate its virtual environment.

## 1. Scaffold an asset

You can use the `dg scaffold defs` command to scaffold a new asset underneath the `defs` folder. In this example, we scaffold an asset named `my_asset.py` and write it to the `defs/assets` directory:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/dagster-definitions/1-scaffold.txt" />

Once the asset has been scaffolded, we can see that a new file has been added to `defs/assets`, and view its contents:

<Tabs>
    <TabItem value="uv">
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/dagster-definitions/2-tree.txt" />
    </TabItem>
    <TabItem value="pip">
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/dagster-definitions/2-tree-pip.txt" />
    </TabItem>
</Tabs>


<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/dagster-definitions/3-cat.txt" />

<DgScaffoldDefsTip />

## 2. Write an asset definition

In the above example, the scaffolded asset contains a basic commented-out definition. You can replace this definition with working code:

<CodeExample path="docs_snippets/docs_snippets/guides/dg/dagster-definitions/4-written-asset.py" title="defs/assets/my_asset.py" />

## 3. Check your work

Finally, you can run `dg list defs` to confirm that the new asset now appears in the list of definitions:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/dagster-definitions/5-list-defs.txt" />
