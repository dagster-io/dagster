---
title: 'Scaffolding traditional Dagster definitions'
sidebar_position: 200
---

import Preview from '../../../partials/\_Preview.md';

<Preview />

`dg` can be used to help scaffold traditional Dagster definitions such as schedules, sensors, and assets. When using a project that has been scaffolded using `dg`, any new definitions added underneath the `defs` directory will be automatically loaded into the top-level `Definitions` object. This allows new definitions to be easily added to a project without needing to explicitly import these definitions to your top-level definitions file.

This guide will walk through how to use `dg` to scaffold a new asset.

# dg scaffold

### 1. Scaffold an asset

You can use the `dg scaffold` command to scaffold a new asset underneath the `defs` folder. For this example, we'll scaffold an asset named `my_asset.py`, and write it to the `defs/assets` directory.

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/dg/dagster-definitions/1-scaffold.txt"  />

Once this is done, we can see that a new file has been added to this location, and view its contents.

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/dg/dagster-definitions/2-tree.txt"  />
<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/dg/dagster-definitions/3-cat.txt"  />

### 2. Write a definition

As seen in the above example, the scaffolded asset contains a basic commented-out definition. We'll want to replace this definition with whatever asset code we're interested in.

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/dg/dagster-definitions/4-written-asset.py"  />

### 3. Checking our work

Finally, if we run `dg list defs`, we can confirm that our new asset now appears in the list of definitions.

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/dg/dagster-definitions/5-list-defs.txt"  />