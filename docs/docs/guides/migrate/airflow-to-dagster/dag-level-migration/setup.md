---
title: 'Setup'
sidebar_position: 100
---

In order the complete this tutorial, you'll need to:

- Create a virtual environment
- Install Dagster and the tutorial example code
- Set up a local Airflow instance

## Create a virtual environment

First, create a fresh virtual environment using `uv` and activate it:

```bash
pip install uv
uv venv
source .venv/bin/activate
```

## Install Dagster and the tutorial example code

Next, install Dagster and verify that the `dagster` CLI is available:

```bash
uv pip install dagster
dagster --version
```

Finally, install the tutorial example code:

```bash
dagster project from-example --name airlift-migration-tutorial --example airlift-migration-tutorial
```

### Project structure

The tutorial example contains the following files and directories:

```plaintext
tutorial_example
├── shared: Contains shared Python & SQL code used Airflow and proxied Dagster code
│
├── dagster_defs: Contains Dagster definitions
│   ├── stages: Contains reference implementations of each stage of the migration process
│   ├── definitions.py: Empty starter file for following along with the tutorial
│
├── airflow_dags: Contains the Airflow DAG and associated files
│   ├── proxied_state: Contains migration state files for each DAG, see migration step below
│   ├── dags.py: The Airflow DAG definition
```

## Set up a local Airflow instance

This tutorial involves running a local Airflow instance, which you can do by following commands from the root of the `airlift-migration-tutorial` directory.

First, install the required Python packages:

```bash
make airflow_install
```

Next, scaffold the Airflow instance and initialize the `dbt` project:

```bash
make airflow_setup
```

Finally, run the Airflow instance with environment variables set:

```bash
make airflow_run
```

This will run the Airflow Web UI in a shell. You should now be able to access the Airflow UI at `http://localhost:8080`, with the default username and password set to `admin`.

You should be able to see the `rebuild_customers_list` DAG in the Airflow UI, made up of three tasks: `load_raw_customers`, `run_dbt_model`, and `export_customers`:

![Rebuild customers list DAG](/images/integrations/airlift/rebuild_customers_dag.png)

## Next steps

In the next step, "[Peer your Airflow instance with a Dagster code location](/guides/migrate/airflow-to-dagster/dag-level-migration/peer)", we'll peer our Dagster installation with our Airflow instance.
