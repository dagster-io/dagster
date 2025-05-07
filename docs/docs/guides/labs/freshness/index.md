---
title: 'Freshness Policies'
sidebar_position: 100
unlisted: True
---
import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

## Overview

Freshness policies help you understand which of your assets have materialized recently and which ones are running behind - a key component of asset health. Freshness policies also communicate expectations for data freshness, allowing downstream asset consumers to determine how often assets are expected to be updated.

For example, freshness policies can help identify stale assets caused by:

- Misconfigured `AutomationCondition`s
- Runs not being scheduled due to an upstream failure
- Runs taking longer than expected to complete

### Wait ... isn't there already a `FreshnessPolicy`?
Yes, there is an existing `FreshnessPolicy` API that has been deprecated for some time. We're opting to reuse the name for the new freshness APIs, which requires us to migrate off the legacy API.

To avoid naming conflicts during this migration, we've prefixed the new APIs, class/variable names and function args with "internal" (for example, `InternalFreshnessPolicy` and `internal_freshness_policy` arg on the `@asset` decorator). Once the migration is complete, the "internal" prefix will be removed and `FreshnessPolicy` will be the name of the new APIs.

## Types of Freshness Policies

Currently, we support time window-based freshness policies, which are suitable for most use cases. We plan to add more policy types in the future.

### Time Window Policy

A time window freshness policy is useful when you expect an asset to have new data or be recalculated with some frequency.

<CodeExample path="docs_snippets/docs_snippets/guides/freshness/time_window_policy.py" language="python" />

The above policy states that there should be a successful materialization of the asset at least every 24 hours for it to be considered fresh. An asset that does not meet this condition will be considered failing its freshness policy.

There is an optional warning window (in this case, 12 hours). If the asset does not successfully materialize within this window, it will enter a `warning` freshness state.

## Setting Freshness Policies

### On Individual Assets

You can configure a freshness policy directly on an asset:

<CodeExample path="docs_snippets/docs_snippets/guides/freshness/individual_asset_policy.py" language="python" />

### Across Multiple Assets

To apply freshness policies to many or all assets in your deployment, you can use `map_asset_specs`:

<CodeExample path="docs_snippets/docs_snippets/guides/freshness/multiple_assets_policy.py" language="python" />

You can also use `map_asset_specs` directly on the asset specs before creating a `Definitions` object:

<CodeExample path="docs_snippets/docs_snippets/guides/freshness/map_asset_specs_direct.py" language="python" />

<aside>
⚠️ Note that applying a freshness policy in this way to an asset with an existing freshness policy (for example, if it was defined in the `@asset` decorator) will overwrite the existing policy.
</aside>

### Limitations

Freshness policies are not currently supported for source observable assets (`SourceAssets`) and cacheable assets (`CacheableAssetsDefinition`).

## Future Enhancements

- More types of freshness policies, including:
    - Cron-based
    - Anomaly detection-based
    - Custom (user-defined) freshness
- Support for source observable assets