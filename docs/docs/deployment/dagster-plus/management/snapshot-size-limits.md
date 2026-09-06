---
description: Dagster+ limits the serialized size of a code location's repository and job snapshots to 130 MB, and how to estimate and reduce your snapshot size.
sidebar_position: 5100
title: Code location snapshot size limits
tags: [dagster-plus-feature]
---

When a code location is deployed, Dagster+ stores a serialized **snapshot** of its
definitions — a repository snapshot describing all of your assets, jobs, schedules,
sensors, and resources, plus a separate snapshot for each job — including the
built-in job Dagster uses to materialize your assets when a run doesn't target a
specific named job. These snapshots are what the Dagster+ UI and agents read to
display and run your definitions.

Each individual snapshot can be at most **130 MB** uncompressed.

In practice you'll usually hit a different limit first. Dagster loads snapshots from
your code server over gRPC, and gRPC messages are limited to **100 MB** by default.
A snapshot larger than that fails to load with a gRPC `RESOURCE_EXHAUSTED` error
before it ever reaches the 130 MB storage limit. You can raise the gRPC limit with
the `DAGSTER_GRPC_MAX_RX_BYTES` and `DAGSTER_GRPC_MAX_SEND_BYTES` environment
variables, which must be set on **both the agent and the code server processes**
(the code server sends the snapshot and the agent receives it, so both ends enforce
the limit). However, rather than working around it, a snapshot that large is best reduced — see
[Reducing snapshot size](#reducing-snapshot-size).

## Estimating your snapshot size locally

You can estimate the serialized size of your repository snapshot and each job
snapshot before deploying, directly from your `Definitions`:

<CodeExample path="docs_snippets/docs_snippets/deployment/dagster_plus/estimate_snapshot_size.py" />

This prints the size of the repository snapshot and of every job snapshot, so you
can see which is approaching the limit.

## Reducing snapshot size

If a snapshot is large or approaching the limit, the most effective levers are
usually, in order:

- **Upgrade Dagster.** Newer versions serialize snapshots more compactly (for
  example, by no longer persisting redundant fields), so upgrading the version your
  code location runs can shrink the snapshot with no changes to your definitions.
- **Reduce repeated per-asset metadata.** Asset metadata is stored on every asset
  node. If the same metadata block is attached to many assets, consider attaching it
  once at a higher level or trimming redundant entries. Large metadata values (long
  descriptions, embedded tables, big tag sets) on individual assets also add up.
- **Split into multiple code locations.** If a single code location genuinely
  defines a large number of assets, splitting it divides the snapshots and lets them
  load in parallel. For more information, see [creating workspaces](/guides/build/projects/workspaces/creating-workspaces).
