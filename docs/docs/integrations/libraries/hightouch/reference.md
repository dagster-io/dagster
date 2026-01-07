---
title: dagster-hightouch integration reference
description: API reference for the Dagster Hightouch integration.
sidebar_position: 500
---
# dagster-hightouch API reference

## Components

The `HightouchSyncComponent` is the modern, declarative way to define Hightouch syncs as Dagster assets.

::: ddoc:dagster_hightouch.components.HightouchSyncComponent

## Resources

### Configurable Resource (Modern)
This is the recommended resource for modern Dagster projects using pythonic configuration.

::: ddoc:dagster_hightouch.resources.ConfigurableHightouchResource

### Legacy Resource
Included for backward compatibility with older Dagster versions.

::: ddoc:dagster_hightouch.resources.HightouchResource

## Ops

The `hightouch_sync_op` allows triggering Hightouch syncs within a Dagster job.

::: ddoc:dagster_hightouch.ops.hightouch_sync_op

## Types

These types define the output schema and metadata returned by Hightouch sync operations.

::: ddoc:dagster_hightouch.types.HightouchOutput
