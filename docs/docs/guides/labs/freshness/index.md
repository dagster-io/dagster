---
title: 'Freshness policies'
description: Dagster Freshness policies help you understand which of your assets have materialized recently and which ones are running behind - a key component of asset health.
sidebar_position: 100
unlisted: True
---

import FreshnessPoliciesPreview from '@site/docs/partials/\_FreshnessPoliciesPreview.md';

<FreshnessPoliciesPreview />

## Overview

Freshness policies help you understand which of your assets have materialized recently and which ones are running behind - a key component of asset health. Freshness policies also communicate expectations for data freshness, allowing downstream asset consumers to determine how often assets are expected to be updated.

For example, freshness policies can help identify stale assets caused by:

- Misconfigured <PyObject section="assets" module="dagster" object="AutomationCondition" pluralize />
- Runs not being scheduled due to an upstream failure
- Runs taking longer than expected to complete

### Relationship to existing `FreshnessPolicy`

There is an existing `FreshnessPolicy` API that has been deprecated for quite some time. We're opting to reuse the name for the new freshness APIs, which requires us to migrate off the legacy API.

To avoid naming conflicts with the legacy API during this migration, we've prefixed the new APIs, class names, and method arguments with "internal", for example, `InternalFreshnessPolicy` and the `internal_freshness_policy` argument on the `@asset` decorator. Once the migration is complete and the new APIs exit preview mode, the "internal" prefix will be removed and `FreshnessPolicy` will be the name of the new APIs.

## Freshness policy types

Currently, we support time window-based freshness policies, which are suitable for most use cases. We plan to add more policy types in the future.

### Time window policy

A time window freshness policy is useful when you expect an asset to have new data, or be recalculated with some frequency. An asset that does not meet this condition will be considered failing its freshness policy. You can set an optional warning window on a freshness policy; if the asset does not successfully materialize within this window, it will enter a `warning` freshness state.

For example, the policy below states that there should be a successful materialization of the asset at least every 24 hours for it to be considered fresh, with a warning window of 12 hours:

<CodeExample path="docs_snippets/docs_snippets/guides/freshness/time_window_policy.py" language="python" />

:::info

- `fail_window` and `warn_window` cannot be shorter than 60 seconds.
- `warn_window` must be less than `fail_window`.

:::

## Setting freshness policies

### On individual assets

You can configure a freshness policy directly on an asset:

<CodeExample path="docs_snippets/docs_snippets/guides/freshness/individual_asset_policy.py" language="python" />

### Across multiple assets

To apply freshness policies to multiple or all assets in your deployment, you can use `map_asset_specs`:

<CodeExample path="docs_snippets/docs_snippets/guides/freshness/multiple_assets_policy.py" language="python" />

You can also use `map_asset_specs` directly on the asset specs before creating a `Definitions` object:

<CodeExample path="docs_snippets/docs_snippets/guides/freshness/map_asset_specs_direct.py" language="python" />

:::caution

Applying a freshness policy in this way to an asset with an existing freshness policy (for example, if it was defined in the `@asset` decorator) will overwrite the existing policy.

:::

### Limitations

Freshness policies are not currently supported for source observable assets (<PyObject section="assets" module="dagster" object="SourceAsset" pluralize />) and cacheable assets (`CacheableAssetsDefinition`).

## Future enhancements

- More freshness policy types, including:
  - Cron-based
  - Anomaly detection-based
  - Custom (user-defined) freshness
- Support for source observable assets
