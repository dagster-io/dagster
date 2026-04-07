---
title: Define assets
description: Define IBM DataStage replication jobs as Dagster multi-assets with inline data quality checks
last_update:
  author: Dennis Hume
sidebar_position: 20
---

[IBM DataStage](https://www.ibm.com/products/datastage) runs replication jobs that move tables from a source system to a target. In this example, a single job replicates five tables from a DB2 mainframe to Snowflake. Rather than treating this as one opaque asset, we model each table as its own Dagster asset so that the asset catalog reflects the actual data being produced.

The code is organized into four building blocks:

1. A translator that maps DataStage tables to Dagster concepts
2. A resource that drives the [`cpdctl`](https://github.com/IBM/cpdctl/) CLI
3. A multi-asset factory that turns the table list into specs
4. A `DataStageProject` component that assembles everything from YAML

## The translator

`DataStageTranslator` converts each table definition into the Dagster asset attributes (key, group, description, and tags):

<CodeExample
  path="docs_projects/project_datastage/src/project_datastage/components/data_stage_job_component.py"
  language="python"
  startAfter="start_datastage_translator"
  endBefore="end_datastage_translator"
  title="src/project_datastage/components/data_stage_job_component.py"
/>

The translator is a `@dataclass`, so subclassing and overriding individual methods is straightforward. For example, you can change `get_asset_key` to use a different key prefix for your organization's naming conventions without touching any other logic.

## The resource

`DataStageResource` is a <PyObject section="resources" module="dagster" object="ConfigurableResource"/> that exposes a single `run` method dispatching to a demo or production path based on the `demo_mode` flag. In both paths it yields a `MaterializeResult` and two `AssetCheckResult` objects per table — all from the same step.

The class definition, `run` dispatcher, and demo path are shown below. Demo mode simulates a successful replication with random row counts so the pipeline can be run locally without a `cpdctl` installation:

<CodeExample
  path="docs_projects/project_datastage/src/project_datastage/components/data_stage_job_component.py"
  language="python"
  startAfter="start_datastage_resource"
  endBefore="end_datastage_resource"
  title="src/project_datastage/components/data_stage_job_component.py"
/>

The production path is extracted into a standalone function that calls three `cpdctl dsjob` commands in sequence: `run --wait 1800` to trigger the job and block until it finishes, `jobinfo --full` to read per-table row counts from the output, and `logdetail` to retrieve the full job log for auditing:

<CodeExample
  path="docs_projects/project_datastage/src/project_datastage/components/data_stage_job_component.py"
  language="python"
  startAfter="start_datastage_resource_production"
  endBefore="end_datastage_resource_production"
  title="src/project_datastage/components/data_stage_job_component.py"
/>

Running checks inline with materialization means the checks always reflect the data that was just loaded. There is no window between materialization and checking during which the data could change.

## The multi-asset factory

`datastage_assets` is a decorator factory that builds a <PyObject section="assets" module="dagster" object="multi_asset"/> from the table list in the project configuration. It creates one `AssetSpec` per table and two `AssetCheckSpec` per table, a row count check and a freshness check:

<CodeExample
  path="docs_projects/project_datastage/src/project_datastage/components/data_stage_job_component.py"
  language="python"
  startAfter="start_datastage_assets"
  endBefore="end_datastage_assets"
  title="src/project_datastage/components/data_stage_job_component.py"
/>

Using a factory function keeps the asset definition tightly coupled to the project configuration. Adding a new table to the YAML automatically produces a new asset and its associated checks without any changes to the Python code.

## The component

`DataStageJobComponent` ties the translator, resource, and multi-asset factory together as a reusable [Dagster component](/guides/build/components/). Its `build_defs` method constructs all Dagster definitions from the component's YAML attributes:

<CodeExample
  path="docs_projects/project_datastage/src/project_datastage/components/data_stage_job_component.py"
  language="python"
  startAfter="start_datastage_component"
  endBefore="end_datastage_component"
  title="src/project_datastage/components/data_stage_job_component.py"
/>

## Next steps

- Continue this example with [scheduling](/examples/full-pipelines/datastage/scheduling)
