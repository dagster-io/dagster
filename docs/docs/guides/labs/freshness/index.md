---
title: 'Asset Freshness'
sidebar_position: 10
---
import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

## Overview

Freshness policies help you understand which of your assets have materialized recently and which ones are running behind - a key component of asset health. Freshness policies also communicate expectations for data freshness, allowing downstream asset consumers to determine how often assets are expected to be updated.

For example, freshness policies can help identify stale assets caused by:

- Misconfigured `AutomationCondition`s
- Runs not being scheduled due to an upstream failure
- Runs taking longer than expected to complete

## Types of Freshness Policies

Currently, we support time window-based freshness policies, which are suitable for most use cases. We plan to add more policy types in the future.

### Time Window Policy

A time window freshness policy is useful when you expect an asset to have new data or be recalculated with some frequency.

```python
from datetime import timedelta
from dagster._core.definitions.freshness import InternalFreshnessPolicy, TimeWindowFreshnessPolicy

# Create a policy that requires updates every 24 hours
policy = TimeWindowFreshnessPolicy.from_timedeltas(
    fail_window=timedelta(hours=24),
    warn_window=timedelta(hours=12)  # optional, must be less than fail_window
)

# Or, equivalently, from the base class
policy = InternalFreshnessPolicy.time_window(
    fail_window=timedelta(hours=24),
    warn_window=timedelta(hours=12)
)
```

The above policy states that there should be a successful materialization of the asset at least every 24 hours for it to be considered fresh. An asset that does not meet this condition will be considered failing its freshness policy.

There is an optional warning window (in this case, 12 hours). If the asset does not successfully materialize within this window, it will enter a `warning` freshness state.

## Setting Freshness Policies

### On Individual Assets

You can configure a freshness policy directly on an asset:

```python
from datetime import timedelta
from dagster._core.definitions.freshness import InternalFreshnessPolicy
from dagster._core.definitions.decorators.asset_decorator import asset
from dagster._core.definitions.asset_spec import AssetSpec

policy = InternalFreshnessPolicy.time_window(
    fail_window=timedelta(hours=24)
)

@asset(internal_freshness_policy=policy)
def my_asset(): ...

# Or on an asset spec
spec = AssetSpec(..., internal_freshness_policy=policy)
```

### Across Multiple Assets

To apply freshness policies to many or all assets in your deployment, you can use `map_asset_specs`:

```python
from dagster import asset, AssetsDefinition
from dagster._core.definitions.asset_spec import attach_internal_freshness_policy
from dagster._core.definitions.freshness import InternalFreshnessPolicy
from datetime import timedelta

@asset
def asset_1(): ...

@asset
def asset_2(): ...

policy = InternalFreshnessPolicy.time_window(
    fail_window=timedelta(hours=24)
)

defs = Definitions(assets=[asset_1, asset_2])
defs.map_asset_specs(
    func=lambda spec: attach_internal_freshness_policy(spec, freshness_policy)
)

# Or, you can optionally provide an asset selection string
defs.map_asset_specs(
    func=lambda spec: attach_internal_freshness_policy(spec, freshness_policy),
    selection="asset_1" # will only apply policy to asset_1
)
```

You can also use `map_asset_specs` directly on the asset specs before creating a `Definitions` object:
```python
from dagster._core.definitions.asset_spec import attach_internal_freshness_policy
from dagster._core.definitions.freshness import InternalFreshnessPolicy
from datetime import timedelta


@asset
def asset_1(): ...

@asset
def asset_2(): ...

policy = InternalFreshnessPolicy.time_window(fail_window=timedelta(hours=24))

assets = [asset_1, asset_2]
assets_with_policies = map_asset_specs(func=lambda spec: attach_internal_freshness_policy(spec, freshness_policy))

defs = Definitions(assets=assets_with_policies)
```

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