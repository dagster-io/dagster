---
title: "Kind tags"
description: "Use kind tags to easily categorize assets within your Dagster project."
sidebar_position: 2000
---

Kind tags can help you quickly identify the underlying system or technology used for a given asset in the Dagster UI. These tags allow you to organize assets within a Dagster project and can be used to filter or search across all your assets.

## Adding kinds to an asset

You may add up to three kinds to the `kinds` argument of an <PyObject section="assets" module="dagster" object="asset" decorator />, which can be useful to represent multiple technologies or systems that an asset is associated with. For example, an asset which is built by Python code and stored in Snowflake can be tagged with both `python` and `snowflake` kinds:

<CodeExample path="docs_snippets/docs_snippets/concepts/metadata-tags/asset_kinds.py" />

Kinds can also be specified on an <PyObject section="assets" module="dagster" object="AssetSpec" />, for use in multi-assets:

<CodeExample path="docs_snippets/docs_snippets/concepts/metadata-tags/asset_kinds_multi.py" />

On the backend, these kind inputs are stored as tags on the asset. For more information, see [Tags](/guides/build/assets/metadata-and-tags/index.md#tags).

When viewing the asset in the lineage view, the attached kinds will be visible at the bottom the asset.

<img
  src="/images/guides/build/assets/metadata-tags/kinds/kinds.svg"
  alt="Asset in lineage view with attached kind tags"
/>

## Adding compute kinds to assets

:::warning

Using `compute_kind` has been superseded by the `kinds` argument. We recommend using the `kinds` argument instead.

:::

You can add a single compute kind to any asset by providing a value to the `compute_kind` argument.

```python
@asset(compute_kind="dbt")
def my_asset():
    pass
```

## Supported icons

Some kinds are given a branded icon in the UI. We currently support nearly 200 unique technology icons.

import KindsTags from '@site/docs/partials/\_KindsTags.md';

<KindsTags />

## Requesting additional icons

The kinds icon pack is open source and anyone can [contribute new icons](/about/contributing) to the public repo or request a new icon by [filing an issue](https://github.com/dagster-io/dagster/issues/new?assignees=&labels=type%3A+feature-request&projects=&template=request_a_feature.ym). Custom icons per deployment are not currently supported.
