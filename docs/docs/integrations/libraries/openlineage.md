---
title: Dagster & OpenLineage
sidebar_label: OpenLineage
sidebar_position: 1
description: The community-supported dagster-openlineage package emits asset-centric OpenLineage events from Dagster — including schema, column-lineage, data-quality-assertion, and partition nominal-time facets.
tags: [community-supported, metadata]
source: https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-openlineage
pypi: https://pypi.org/project/dagster-openlineage/
sidebar_custom_props:
  logo: images/integrations/openlineage.svg
  community: true
partnerlink: https://openlineage.io/
---

import CommunityIntegration from '@site/docs/partials/\_CommunityIntegration.md';

<CommunityIntegration />

<p>{frontMatter.description}</p>

## Installation

<PackageInstallInstructions packageName="dagster-openlineage" />

## Which mechanism should I use?

`dagster-openlineage` v0.2 provides two emission mechanisms — configure **exactly one** per deployment:

| Environment | Mechanism A (storage wrapper) | Mechanism B (sensor) |
|---|---|---|
| OSS Dagster (self-hosted) | ✅ | ✅ |
| Dagster+ Hybrid | ❌ | ✅ |
| Dagster+ Serverless | ❌ | ✅ |
| Dagster+ Branch Deployments | ❌ | ✅ |

- **You control `instance.yaml`** → use Mechanism A. Every event is emitted as it is persisted; no daemon dependency.
- **You run on Dagster+** → use Mechanism B. The sensor polls the event log and converts asset events to OpenLineage emissions.

## Mechanism A — storage wrapper

Configure `OpenLineageEventLogStorage` in `instance.yaml`. It wraps any inner `EventLogStorage` and intercepts writes to emit OpenLineage events for every asset materialization, observation, check evaluation, and synthesized failure.

```yaml
# instance.yaml
event_log_storage:
  module: dagster_openlineage
  class: OpenLineageEventLogStorage
  config:
    wrapped:
      module: dagster_postgres.event_log
      class: PostgresEventLogStorage
      config:
        postgres_url:
          env: DAGSTER_PG_URL
    namespace: my-company
    # Optional — namespace_template overrides the static namespace field.
    # Note: the {tag:KEY} token always resolves to an empty string in
    # Mechanism A because EventLogStorage has no access to run tags at
    # store_event time. Use Mechanism B if you need per-run tag resolution.
    # namespace_template: "{namespace}"
    # timeout: 2.0
```

Set `OPENLINEAGE_URL` (and optionally `OPENLINEAGE_API_KEY`) in the environment of any process that writes Dagster events — typically the run worker and the daemon.

## Mechanism B — sensor

Add `openlineage_sensor(include_asset_events=True)` to your `Definitions`. The sensor runs in the Dagster daemon and has full access to run tags, making it the right choice for `{tag:KEY}` namespace resolution and Dagster+ deployments.

```python
from dagster import Definitions
from dagster_openlineage import openlineage_sensor

defs = Definitions(
    assets=[...],
    sensors=[openlineage_sensor(include_asset_events=True)],
)
```

Set these environment variables on the process that runs the Dagster daemon:

- `OPENLINEAGE_URL` (required)
- `OPENLINEAGE_API_KEY` (optional)
- `OPENLINEAGE_NAMESPACE` (optional, default `dagster`)

## Features

- **Asset-centric emission** — materializations, observations, check evaluations, and synthesized failures emitted as OpenLineage `RunEvent` / `DatasetEvent`
- **Schema facet** from `dagster/column_schema` metadata
- **Column lineage facet** from `dagster/column_lineage` metadata
- **Data quality assertions** placed on `InputDataset` (spec-conformant)
- **Partition → nominal time** heuristic (ISO date or date-hour partitions)
- **Multi-tenant namespaces** via `{namespace}` and `{tag:KEY}` template tokens
- **Pipeline and step events** preserved (v0.1 surface unchanged)

## Namespace templates

Use `namespace_template` to route assets to per-tenant namespaces. The `{tag:KEY}` token resolves to the run tag named `KEY`, and is only available in **Mechanism B** (the sensor has access to run tags). In Mechanism A it always resolves to an empty string.

```
# Template: "{namespace}/{tag:tenant}"
# (Mechanism B, OPENLINEAGE_NAMESPACE=dagster)
# Run tags {"tenant": "acme"} → resolved namespace "dagster/acme"
# Run tags {}                 → resolved namespace "dagster"  (tag unset, trailing slash stripped)
```

## Migration from v0.1

If you are upgrading from `dagster-openlineage` v0.1 to v0.2, note the following breaking changes:

- **Dagster version:** The minimum supported Dagster version is now `1.11.6`.
- **Default namespace:** The default namespace is now flat (`dagster`). In v0.1, the integration attempted to use the repository name as the namespace. If you wish to preserve the old behavior, configure the `namespace` or `namespace_template` option accordingly.
- **Removed class:** The legacy `OpenLineageEventListener` has been removed.
- **Emission mechanics:** v0.1 emitted pipeline and step events automatically with no extra configuration. In v0.2, you must explicitly configure exactly one mechanism (A or B). Both now include full asset-centric support.

## About OpenLineage

[OpenLineage](https://openlineage.io/) is an open standard for data lineage collection and analysis. It defines a common API for capturing lineage metadata and a set of facets for enriching lineage events with schema, column-level lineage, data quality results, and more. Compatible backends include [Marquez](https://marquezproject.ai/), [Apache Atlas](https://atlas.apache.org/), [DataHub](https://datahubproject.io/), and [OpenMetadata](https://open-metadata.org/).
