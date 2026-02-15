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

The [dagster-soda](/integrations/libraries/soda) library integrates [Soda Core](https://docs.soda.io/soda-core/) data quality checks with Dagster. It provides the **SodaScanComponent**, a Dagster component that runs Soda Core scans and maps SodaCL check results to Dagster asset checks.

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
```

- **checks_paths**: List of paths to SodaCL YAML files (relative to the component directory or project root).
- **configuration_path**: Path to Soda’s `configuration.yml` (data source connection, etc.). See [Soda configuration](https://docs.soda.io/soda-core/configuration.html).
- **data_source_name**: Name of the data source defined in `configuration.yml`.
- **asset_key_map**: Maps Soda dataset/table names to Dagster asset keys. Each key is the dataset name used in your SodaCL `checks for <dataset>:`; the value is the Dagster `AssetKey` (string or tuple).

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

## Loading definitions

Once `defs.yaml` and `checks.yml` (and your Soda `configuration.yml`) are in place, load your definitions as usual. The component contributes asset checks that run Soda scans and surface results in the Dagster UI.
