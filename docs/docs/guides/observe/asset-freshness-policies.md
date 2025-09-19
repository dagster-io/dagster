---
title: Asset freshness policies
description: Dagster+ freshness policies help you understand which of your assets have materialized recently and which ones are running behind - a key component of asset health.
sidebar_position: 400
---

import FreshnessPoliciesPreview from '@site/docs/partials/\_FreshnessPoliciesPreview.md';

<FreshnessPoliciesPreview />

Freshness policies help you understand which of your assets have materialized recently and which ones are running behind - a key component of asset health. Freshness policies also communicate expectations for data freshness, allowing downstream asset consumers to determine how often assets are expected to be updated.

For example, freshness policies can help identify stale assets caused by:

- Misconfigured <PyObject section="assets" module="dagster" object="AutomationCondition" pluralize />
- Runs not being scheduled due to an upstream failure
- Runs taking longer than expected to complete

:::info Asset freshness alerts

You can set an [asset freshness alert](/guides/observe/alerts/creating-alerts) to notify you when an asset is failing its freshness policy.

:::

### Enabling freshness policies

Freshness policies are not enabled by default while in preview. To use them in open source and local development, add the following to your `dagster.yaml`:

```
freshness:
  enabled: True
```

### Relationship to existing `FreshnessPolicy`

There is an existing `FreshnessPolicy` API that has been deprecated since version 1.6. We're opting to reuse the name for the new freshness APIs, and have renamed the deprecated functionality to `LegacyFreshnessPolicy`. To continue using the deprecated functionality, follow the instructions in the [1.11 migration guide](/migration/upgrading#upgrading-to-1110).

### Relationship to freshness checks

Freshness policies are not yet feature complete, but are intended to supersede freshness checks in a future release. Freshness checks are still and will continue to be supported for the foreseeable future. A migration guide will be provided.

## Freshness policy types

Currently, we support [time window](#time-window) and [cron](#cron) freshness policies, which are suitable for most use cases.

### Time window

A time window freshness policy is useful when you expect an asset to have new data or be recalculated with some frequency. An asset that does not meet this condition will be considered failing its freshness policy. You can set an optional warning window on a freshness policy; if the asset does not successfully materialize within this window, it will enter a `warning` freshness state.

For example, the policy below states that there should be a successful materialization of the asset at least every 24 hours for it to be considered fresh, with a warning window of 12 hours:

<CodeExample path="docs_snippets/docs_snippets/guides/freshness/time_window_policy.py" language="python" />

:::info

- `fail_window` and `warn_window` cannot be shorter than 60 seconds.
- `warn_window` must be less than `fail_window`.

:::

### Cron

A cron freshness policy is useful when you expect an asset to have new data or be recalculated on a known schedule.

The policy defines a cron schedule `deadline_cron` that denotes the deadline for the asset materialization.
To account for the time it takes to materialize the asset, a `lower_bound_delta` time delta is also specified,
which denotes an amount of time prior to each cron tick.
Together, `deadline_cron` and `lower_bound_delta` define a recurring time window in which the asset is expected to materialize.

The asset is fresh if it materializes in this time window, and will remain fresh until at least the next deadline.
If the asset has not materialized in the window after the deadline passes, it will fail freshness until it materializes again.

Example:

<CodeExample path="docs_snippets/docs_snippets/guides/freshness/cron_policy.py" language="python" />

:::info

- `deadline_cron` must be a valid cron string and has a minimum resolution of 1 minute.
- `lower_bound_delta` cannot be shorter than 1 minute, and must fit within the smallest interval of `deadline_cron`.
  Example: for `deadline_cron="0 10 * * 1-5"` (weekdays at 10am), `lower_bound_delta` must be between 1 minute and 24 hours.
- `timezone` is optional. [IANA timezones](https://www.iana.org/time-zones) are supported. If not provided, defaults to UTC.

:::

## Setting freshness policies

### On individual assets

You can configure a freshness policy directly on an asset:

<CodeExample path="docs_snippets/docs_snippets/guides/freshness/individual_asset_policy.py" language="python" />

### Across multiple assets

To apply freshness policies to multiple or all assets in your deployment, you can use `map_asset_specs`.
Use `map_resolved_asset_specs` to apply a policy to an asset selection.

<CodeExample path="docs_snippets/docs_snippets/guides/freshness/multiple_assets_policy.py" language="python" />

You can also use `map_asset_specs` directly on the asset specs before creating a `Definitions` object:

<CodeExample path="docs_snippets/docs_snippets/guides/freshness/map_asset_specs_direct.py" language="python" />

:::caution

Applying a freshness policy in this way to an asset with an existing freshness policy (for example, if it was defined in the `@asset` decorator) will overwrite the existing policy.

:::

### Setting a default freshness policy

Often, it's useful to set a default freshness policy across all assets, and override the default on individual assets.

To do so, you can use `map_asset_specs` with `overwrite_existing` set to `False` on the mapped function to avoid overwriting any pre-defined freshness policies:

<CodeExample path="docs_snippets/docs_snippets/guides/freshness/default_freshness.py" language="python" />

### Limitations

Freshness policies are not currently supported for source observable assets (<PyObject section="assets" module="dagster" object="SourceAsset" pluralize />) and cacheable assets (`CacheableAssetsDefinition`).

## Future enhancements

- More freshness policy types, including:
  - Anomaly detection-based
  - Custom (user-defined) freshness
- Support for source observable assets
