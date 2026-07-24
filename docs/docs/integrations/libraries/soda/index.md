---
title: Dagster & Soda (Component)
sidebar_label: Soda
sidebar_position: 1
description: The dagster-soda library provides a SodaScanComponent that runs Soda Core scans and maps SodaCL check results to Dagster asset checks.
tags: [dagster-supported, data-quality, component]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-soda
pypi: https://pypi.org/project/dagster-soda
canonicalUrl: '/integrations/libraries/soda'
slug: '/integrations/libraries/soda'
---

The [dagster-soda](/integrations/libraries/soda) library integrates [Soda Core](https://docs.soda.io/soda-documentation/soda-v3/overview-main) data quality checks with Dagster. It provides the **SodaScanComponent**, a Dagster component that runs Soda Core scans and maps SodaCL check results to Dagster asset checks.

## Installation

<PackageInstallInstructions packageName="dagster-soda" />

:::note

`dagster-soda` requires **soda-core 3.x** (the `soda.scan` API). The library pins `soda-core>=3.0,<4` by default.

:::

## Overview

Configure a `SodaScanComponent` in your Dagster project to:

- Point at SodaCL YAML check files and a Soda `configuration.yml`
- Map Soda dataset names to Dagster asset keys
- Run scans and report pass/fail as Dagster asset check results

## Scaffolding with the CLI

Use the Dagster CLI to scaffold a new Soda scan component in your project. This requires [dagster-dg-cli](https://docs.dagster.io/concepts/components#scaffolding-components).

```bash
dg scaffold defs dagster_soda.SodaScanComponent <path>
```

Example — scaffold into a folder named `soda_checks` under your defs directory:

```bash
dg scaffold defs dagster_soda.SodaScanComponent soda_checks
```

This generates:

- A **defs.yaml** with default attributes (`checks_paths`, `configuration_path`, `data_source_name`, `asset_key_map`)
- A **checks.yml** template with example SodaCL (e.g. `checks for my_table: - row_count > 0`)

Edit the generated files to match your data source and checks, then load your definitions as usual.

## Configuration

### defs.yaml example

After scaffolding, update `defs.yaml` with your paths, data source name, and asset key mapping:

```yaml
type: dagster_soda.SodaScanComponent
attributes:
  checks_paths:
    - checks.yml
  configuration_path: configuration.yml
  data_source_name: my_datasource
  asset_key_map:
    my_table: my_table
  # Optional:
  # default_severity: warn
```

### Attributes reference

| Attribute            | Type             | Required | Default  | Description                                                                                                                                                                                                                                               |
| -------------------- | ---------------- | -------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `checks_paths`       | `list[str]`      | Yes      | —        | List of paths to SodaCL YAML check files, relative to the component directory or project root (absolute paths are also accepted). Paths that don't exist are skipped.                                                                                     |
| `configuration_path` | `str`            | Yes      | —        | Path to Soda's `configuration.yml` (data source connection, etc.). See [Soda configuration](https://docs.soda.io/soda-core/configuration.html).                                                                                                           |
| `data_source_name`   | `str`            | Yes      | —        | Name of the data source defined in `configuration.yml`.                                                                                                                                                                                                   |
| `asset_key_map`      | `dict[str, str]` | No       | `{}`     | Maps Soda dataset/table names to Dagster asset keys. Each key is the dataset name used in your SodaCL `checks for <dataset>:`; the value is the Dagster `AssetKey` (string form, e.g. `"my_table"` or `"prefix/my_table"`). See the filtering note below. |
| `default_severity`   | `str`            | No       | `"warn"` | Severity applied to a check result when Soda doesn't report one. `error` (or `fail`) maps to `AssetCheckSeverity.ERROR`; any other value maps to `AssetCheckSeverity.WARN`.                                                                               |

:::note

`asset_key_map` also controls which datasets produce [asset checks](/guides/test/asset-checks). When the map is empty (the default), the component creates asset checks for every dataset found in your `checks_paths`, using each dataset name directly as its `AssetKey`. When the map is non-empty, the component only creates asset checks for the datasets listed in the map — datasets not present in the map are ignored.

:::

### checks.yml example

The scaffolded **checks.yml** is a SodaCL file. Replace `my_table` with your actual dataset/table names and add checks as needed:

```yaml
# SodaCL checks for your datasets
# See https://docs.soda.io/soda-cl/soda-cl-overview.html for SodaCL syntax
#
# Add asset_key_map in defs.yaml to map Soda dataset names to Dagster AssetKeys.

checks for my_table:
  - row_count > 0
  # - freshness(updated_at) < 1d
  # - schema:
  #     fail:
  #       when required column missing: [id, name]
```

For more SodaCL options, see the [SodaCL documentation](https://docs.soda.io/soda-cl/soda-cl-overview.html).

## Supported checks

`SodaScanComponent` runs any check that [SodaCL](https://docs.soda.io/soda-cl/soda-cl-overview.html) supports on **soda-core 3.x** — it doesn't define its own check types. Each check you write in `checks_paths` becomes an individual Dagster asset check on the mapped asset. The table below summarizes the check types you can use, with a SodaCL example for each.

| Check type                   | Validates                                                                             | SodaCL example                                                               |
| ---------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **Row count**                | Table has an expected number of rows.                                                 | `row_count > 0`<br />`row_count between 10 and 1000`                         |
| **Missing values**           | A column has no (or few) nulls / missing values.                                      | `missing_count(id) = 0`<br />`missing_percent(email) < 5%`                   |
| **Duplicates**               | A column (or column set) has no (or few) duplicate values.                            | `duplicate_count(order_id) = 0`<br />`duplicate_percent(email) < 1%`         |
| **Validity**                 | Column values match an allowed format, value set, range, or length.                   | `invalid_count(email) = 0:`<br />`  valid format: email`                     |
| **Numeric aggregates**       | An aggregate (`avg`, `min`, `max`, `sum`, `stddev`, `percentile`, …) is within range. | `avg(price) between 1 and 1000`<br />`max(score) <= 100`                     |
| **Freshness**                | The most recent row is newer than a threshold.                                        | `freshness(updated_at) < 1d`                                                 |
| **Schema**                   | Required columns exist (and, optionally, have expected types).                        | `schema:`<br />`  fail:`<br />`    when required column missing: [id, name]` |
| **Reference**                | Referential integrity — values exist in another dataset.                              | `values in (customer_id) must exist in customers (id)`                       |
| **Cross checks**             | A metric matches the same metric in another dataset.                                  | `row_count same as other_table`                                              |
| **Failed rows / custom SQL** | Arbitrary row-level conditions expressed in SQL.                                      | `failed rows:`<br />`  fail condition: status not in ('active', 'inactive')` |

For the exact syntax, thresholds (`warn`/`fail`), filters, and per-check configuration (e.g. `valid values`, `missing values`, custom names), see the [SodaCL reference](https://docs.soda.io/soda-cl/metrics-and-checks.html).

:::note

Anomaly detection and distribution checks are part of SodaCL, but need extra setup beyond a plain scan. Anomaly checks require a [Soda Cloud](https://docs.soda.io/soda-cloud/overview.html) connection to store historical measurements, and distribution checks require a distribution reference object (DRO). The component runs them if configured, but a standalone `configuration.yml` alone isn't sufficient.

:::

### How check results map to Dagster

For each dataset (mapped via `asset_key_map`), the component emits one asset check per SodaCL check:

- A Soda `pass` outcome becomes a passing `AssetCheckResult`; `warn` or `fail` becomes a failing result.
- Severity comes from the Soda check (its `warn`/`fail` threshold), falling back to `default_severity` — `error`/`fail` maps to `AssetCheckSeverity.ERROR`, otherwise `AssetCheckSeverity.WARN`.
- The Soda outcome, severity, check name, and check definition are attached as asset check metadata, visible in the Dagster UI.

## Loading definitions

Once `defs.yaml` and `checks.yml` (and your Soda `configuration.yml`) are in place, load your definitions as usual. The component contributes asset checks that run Soda scans and surface results in the Dagster UI.
