---
title: 'Adding Dagster definitions to a dg project'
description: Dagster dg can be used to scaffold Dagster definitions such as assets, schedules, and sensors.
sidebar_label: 'Adding Dagster definitions'
sidebar_position: 200
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

`dg` can be used to scaffold Dagster definitions such as [assets](/guides/build/assets/), [schedules](/guides/automate/schedules/), and [sensors](/guides/automate/sensors/). When you use a project that has been scaffolded using `dg`, any new definitions added underneath the `defs` directory will be automatically loaded into the top-level `Definitions` object. This allows you to easily add new definitions to your project without needing to explicitly import these definitions to your top-level definitions file.

This guide will walk through how to use `dg` to scaffold a new asset.

## Scaffold an asset

You can use the `dg scaffold` command to scaffold a new asset underneath the `defs` folder. In this example, we scaffold an asset named `my_asset.py` and write it to the `defs/assets` directory:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/dagster-definitions/1-scaffold.txt" />

Once this is done, we can see that a new file has been added to this location, and view its contents:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/dagster-definitions/2-tree.txt" />
<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/dagster-definitions/3-cat.txt" />

### Write a definition

As seen in the above example, the scaffolded asset contains a basic commented-out definition. We can replace this definition with whatever asset code we're interested in:

<CodeExample path="docs_snippets/docs_snippets/guides/dg/dagster-definitions/4-written-asset.py" />

### Check your work

Finally, we can run `dg list defs` to confirm that the new asset now appears in the list of definitions:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/dagster-definitions/5-list-defs.txt" />
