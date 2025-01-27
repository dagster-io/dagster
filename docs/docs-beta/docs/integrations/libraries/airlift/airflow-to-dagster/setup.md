---
title: "Set up a local environment"
sidebar_position: 100
---

In this step, we'll

- Install the example code
- Set up a local environment
- Ensure we can run Airflow locally.

## Installation & project structure

First, we'll create a fresh virtual environment using `uv`.

```bash
pip install uv
uv venv
source .venv/bin/activate
```

Next, we'll install Dagster, and verify that the dagster CLI is available.

```bash
uv pip install dagster
dagster --version
```

First, we'll create a fresh virtual environment using `uv`.

```bash
dagster project from-example --name airlift-migration-tutorial --example airlift-migration-tutorial
```

### Project structure

The following explains the structure of the repo.

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

## Running Airflow locally

The tutorial example involves running a local Airflow instance. This can be done by running the following commands from the root of the `airlift-migration-tutorial` directory.

First, install the required python packages:

```bash
make airflow_install
```

Next, scaffold the Airflow instance, and initialize the dbt project:

```bash
make airflow_setup
```

Finally, run the Airflow instance with environment variables set:

```bash
make airflow_run
```

This will run the Airflow Web UI in a shell. You should now be able to access the Airflow UI at `http://localhost:8080`, with the default username and password set to `admin`.

You should be able to see the `rebuild_customers_list` DAG in the Airflow UI, made up of three tasks: `load_raw_customers`, `run_dbt_model`, and `export_customers`.

![Rebuild customers list DAG](/images/integrations/airlift/rebuild_customers_dag.png)

## Next steps

The next step is to peer a Dagster installation with the Airflow Instance. [Click here](peer) to follow along for part 2.
