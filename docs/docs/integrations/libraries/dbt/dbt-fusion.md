---
title: Dagster & dbt Fusion
sidebar_label: dbt Fusion
description: Run your dbt project on the dbt Fusion engine with Dagster, including how Dagster selects a dbt executable and which features are not supported on Fusion.
sidebar_position: 300
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

<p>{frontMatter.description}</p>

The dbt Fusion engine is dbt Labs' rewrite of dbt in Rust. Its main benefit for Dagster users is parse time: Fusion compiles a project's manifest substantially faster than the Python implementation, which is most noticeable on large projects and on every code location reload.

Fusion [reached general availability](https://docs.getdbt.com/blog/dbt-v2-is-ga) on September 16, 2026. As part of that release, dbt Labs renamed the Fusion engine to `dbt` and renamed the previous Python implementation to `dbt OSS`. This page uses "Fusion" and "dbt Core" throughout, since those are the names most existing Dagster projects were built against.

Dagster invokes dbt through the dbt executable, so moving a project to Fusion only requires ensuring the executable your code location resolves is the Fusion executable. There is no feature flag to turn on and nothing to configure in Dagster+.

## Requirements

Fusion support landed in the `dagster` 1.11.5 release. Use `dagster-dbt` 0.29.12 or later, which ships alongside `dagster` 1.13.12, to pick up the Fusion fixes released since then.

## How Dagster selects a dbt executable

`DbtCliResource` chooses an executable in this order:

1. The `dbt_executable` argument, if you set one.
2. An executable named `dbtf` on `PATH`.
3. An executable named `dbt` on `PATH`.

Dagster resolves this through `PATH` in the process that runs your code location.

A few code paths use the absence of `dbt-core` as the signal that they are running against Fusion. If `dbt-core` stays installed, those code paths behave as though you were on dbt Core. See [Limitations](#limitations) for more information.

## Set up a project on Fusion

Install Fusion following the [dbt installation documentation](https://docs.getdbt.com/docs/local/install-dbt).

`dagster-dbt` declares `dbt-core` as a dependency, so installing `dagster-dbt` also installs dbt Core and puts its `dbt` entrypoint in your environment, where it can shadow the Fusion binary. We do not recommend uninstalling `dbt-core`. Any later resolution of project dependencies will pull it back in. This is tracked in [#33513](https://github.com/dagster-io/dagster/issues/33513).

Set up your Dagster project to use the dbt Fusion executable by doing one of the following:

- [Add a dbtf executable to PATH](#add-a-dbtf-executable-to-path)
- [Set the executable explicitly](#set-the-executable-explicitly)

### Add a dbtf executable to PATH

Adding a `dbtf` executable to `PATH` is required to use dbt Fusion with `DbtProjectComponent`, which constructs its own `DbtCliResource` and exposes no executable setting.

`dbtf` is a name Dagster looks for, not one any dbt installer provides, so you create it yourself. The dbt installer does define `dbtf`, but as a shell alias, and Dagster cannot see a shell alias. Add a real executable or symlink to `PATH` instead:

```bash
ln -s /path/to/fusion/dbt ~/.local/bin/dbtf
```

Dagster prefers `dbtf` over `dbt`, so this selects Fusion regardless of what `dbt` resolves to. Do this in your image build so it holds for the process that runs your code location.

### Set the executable explicitly

If you construct `DbtCliResource` yourself, you can instead point it at the Fusion binary by absolute path:

```python
from dagster_dbt import DbtCliResource

dbt = DbtCliResource(
    project_dir="/path/to/dbt/project",
    dbt_executable="/path/to/fusion/dbt",
)
```

## Limitations

Dagster's Fusion support is in preview and has known gaps. Confirm that none of the following block your project before you migrate.

### Column metadata and column lineage are not supported

Column-level metadata and column lineage are not supported on Fusion, and neither is `fetch_row_counts()`. Both are fetched through dbt Core's adapter, and Dagster does not initialize an adapter when the dbt executable reports a 2.x version. Calling either one on Fusion raises an error that fails the step rather than skipping the metadata.

If your project depends on column lineage in the Dagster+ asset graph, weigh that against the parse-time gain before migrating. Track [#34227](https://github.com/dagster-io/dagster/issues/34227) for support.

### Isolated models are silently dropped from selection

A model with no `ref()` or `source()` calls can disappear from your asset graph with no error raised. Fusion adds a model to the manifest's `child_map` only when it has at least one parent. This means an isolated model is absent from the Dagster asset graph and any asset selections.

Nothing surfaces this at runtime, so check your manifest for isolated nodes rather than waiting to notice missing assets. Every node in `nodes`, including seeds and snapshots, should appear in `child_map`, either as a key or inside one of its lists:

```python
import json

with open("target/manifest.json") as f:
    manifest = json.load(f)

child_map = manifest["child_map"]
in_graph = set(child_map) | {child for children in child_map.values() for child in children}
isolated = [unique_id for unique_id in manifest["nodes"] if unique_id not in in_graph]
print(isolated)
```

Anything this prints is missing from your asset graph. As a workaround, give the model a `ref()` or `source()` that is filtered out at runtime, for example with `where 1=0`. Tracked in [#33801](https://github.com/dagster-io/dagster/issues/33801).

### Open issues

| Issue                                                        | Description                                                                                             |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| [#33513](https://github.com/dagster-io/dagster/issues/33513) | The `dbt-core` dependency puts a `dbt` entrypoint in the environment that can shadow the Fusion binary. |
| [#34148](https://github.com/dagster-io/dagster/issues/34148) | The dbt Cloud integration raises `KeyError: 'materialized'` when a Fusion run includes seeds.           |
| [#33512](https://github.com/dagster-io/dagster/issues/33512) | A dbt test that passes under Fusion is occasionally reported as a failed asset check.                   |
| [#33753](https://github.com/dagster-io/dagster/issues/33753) | Fusion applies a hardcoded row limit to `dbt seed`.                                                     |
| [#34227](https://github.com/dagster-io/dagster/issues/34227) | Column metadata, column lineage, and row counts are unavailable on Fusion.                              |

### Fusion's own compatibility surface

Fusion has adapter coverage and feature gaps of its own, independent of Dagster. Validate your project against dbt Labs' [Fusion upgrade documentation](https://docs.getdbt.com/docs/dbt-versions/core-upgrade/upgrading-to-fusion) as well.

## Verify your setup

From the environment your code location runs in, confirm that `dbtf` resolves to the Fusion binary. This is the executable Dagster will pick:

```bash
which dbtf
dbtf --version
```

If `which dbtf` finds nothing, Dagster falls back to `dbt`, and your models run on whichever engine that resolves to.
