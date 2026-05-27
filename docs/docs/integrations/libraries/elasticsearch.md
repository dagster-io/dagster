---
title: Dagster & Elasticsearch
sidebar_label: Elasticsearch
sidebar_position: 1
description: The community-supported Elasticsearch integration provides a resource for interacting with Elasticsearch clusters and an IO manager for bulk-indexing Dagster asset outputs as searchable documents.
tags: [community-supported, storage]
source: https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-elasticsearch
pypi: https://pypi.org/project/dagster-elasticsearch/
sidebar_custom_props:
  logo: images/integrations/elasticsearch.svg
  community: true
partnerlink: https://www.elastic.co/elasticsearch
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-elasticsearch" />

Optional extras are available for table-like asset outputs. Install the extras that match the data types your assets return:

<PackageInstallInstructions packageName="dagster-elasticsearch[pandas]" />

<PackageInstallInstructions packageName="dagster-elasticsearch[polars]" />

<PackageInstallInstructions packageName="dagster-elasticsearch[arrow]" />

The underlying `elasticsearch` Python client must match the major version of your Elasticsearch cluster. Pin the client major version in your project if needed, for example `elasticsearch>=8.10,<9` for Elasticsearch 8.x.

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/elasticsearch.py" language="python" />

## Using the Elasticsearch resource

Use `ElasticsearchResource` when an asset or op needs direct access to an Elasticsearch client. Configure it with either:

- `HostsConfig` for self-hosted or generic Elasticsearch endpoints
- `CloudConfig` for Elastic Cloud deployments

Both configuration types support API-key authentication or basic authentication with a username and password. `HostsConfig` also supports bearer auth, certificate authorities, and certificate verification settings.

## Using the Elasticsearch IO manager

Use `ElasticsearchIOManager` to bulk-index asset outputs into Elasticsearch. It supports outputs such as dictionaries, lists of dictionaries, pandas DataFrames, Polars DataFrames or LazyFrames, and PyArrow tables. The `id_field` option, which defaults to `_id`, is used as the Elasticsearch document ID when present.

Common IO manager options include:

| Option | Description |
| --- | --- |
| `index` | Target index name. When `use_alias=True`, this is the stable alias name. |
| `bulk_chunk_size` | Number of documents per bulk request. |
| `max_chunk_bytes` | Optional maximum bulk request size in bytes. |
| `refresh` | Whether to refresh the index after writes. |
| `lazy_load` | Return an iterator from `load_input` instead of loading all hits eagerly. |
| `scan_size` | Page size for scroll-based reads. |

Most IO manager settings can be overridden for individual assets with asset metadata, including `index`, `id_field`, `bulk_chunk_size`, `max_chunk_bytes`, `refresh`, `rollover_strategy`, and `index_config`.

## Alias rollover

Set `use_alias=True` to write each materialization to a fresh physical index and atomically swap a stable alias to the new index. This lets readers and downstream assets query the alias while avoiding partial updates.

Rollover strategies include:

| Strategy | Behavior |
| --- | --- |
| `auto` | Uses the partition key for partitioned assets, otherwise a timestamp. |
| `timestamp` | Appends a UTC timestamp suffix. |
| `run_id` | Appends the Dagster run ID. |
| `partition` | Appends a slugified partition key. |
| `none` | Uses no suffix. |

Use `keep_last` to delete older rollover indices after successful alias swaps.

## Asset checks

The IO manager records materialization metadata such as `index`, `indexed`, `failures`, and `alias`. Use `build_indexed_asset_check` to assert that a materialization indexed at least a minimum number of documents and did not exceed a maximum failure count.

## About Elasticsearch

Elasticsearch is a distributed search and analytics engine for indexing, searching, and analyzing large volumes of data in near real time. Learn more in the [Elasticsearch documentation](https://www.elastic.co/docs/solutions/search).
