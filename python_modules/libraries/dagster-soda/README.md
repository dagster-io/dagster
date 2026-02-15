# dagster-soda

[![PyPI version](https://badge.fury.io/py/dagster-soda.svg)](https://badge.fury.io/py/dagster-soda)

**dagster-soda** integrates [Soda Core](https://docs.soda.io/soda-core/) data quality checks with Dagster. It provides the **SodaScanComponent**, a Dagster component that runs Soda Core scans and maps SodaCL check results to Dagster asset checks.

## Installation

```bash
pip install dagster-soda
```

**Note:** `dagster-soda` requires **soda-core 3.x** (the `soda.scan` API). It pins `soda-core>=3.0,<4` by default.

## Usage

### Component: SodaScanComponent

Configure a `SodaScanComponent` in your Dagster project to:

- Point at SodaCL YAML check files and a Soda `configuration.yml`
- Map Soda dataset names to Dagster asset keys
- Run scans and report pass/fail as Dagster asset check results

### Scaffolding with the CLI

Use the Dagster CLI to scaffold a new Soda scan component in your project (requires [dagster-dg-cli](https://docs.dagster.io/concepts/components#scaffolding-components)):

```bash
dg scaffold defs dagster_soda.SodaScanComponent <path>
```

Example (scaffold into a folder named `soda_checks` under your defs directory):

```bash
dg scaffold defs dagster_soda.SodaScanComponent soda_checks
```

This generates:

- A **defs.yaml** with default attributes (`checks_paths`, `configuration_path`, `data_source_name`, `asset_key_map`)
- A **checks.yml** template with example SodaCL (e.g. `checks for my_table: - row_count > 0`)

Edit the generated files to match your data source and checks, then load your definitions as usual.

### Minimal defs.yaml example

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

## Documentation

The docs for **dagster-soda** can be found [here](https://docs.dagster.io/integrations/libraries/soda/dagster-soda).
