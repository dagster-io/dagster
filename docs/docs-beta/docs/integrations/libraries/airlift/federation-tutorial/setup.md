---
title: "Setup"
sidebar_position: 100
---

In this step, we'll

- Install the example code
- Set up a local environment
- Ensure we can run Airflow locally.

## Installation & project structure

First, we'll create a fresh virtual environment using `uv` and activate it.

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

Finally, we'll install the tutorial example code.

```bash
dagster project from-example --name airlift-federation-tutorial --example airlift-federation-tutorial
```

### Project structure

The following explains the structure of the repo.

```plaintext
airlift_federation_tutorial
├── constants.py: Contains constant values used throughout both Airflow and Dagster
├── dagster_defs: Contains Dagster definitions
│   ├── definitions.py: Empty starter file for following along with the tutorial
│   └── stages: Contains reference implementations for each stage of the migration process.
├── metrics_airflow_dags: Contains the Airflow DAGs for the "downstream" airflow instance
└── warehouse_airflow_dags: Contains the Airflow DAGs for the "upstream" airflow instance
```

## Running Airflow locally

The tutorial example involves running a local Airflow instance. This can be done by running the following commands from the root of the `airlift-migration-tutorial` directory.

First, install the required python packages:

```bash
make airflow_install
```

Next, scaffold the two Airflow instances we'll be using for this tutorial:

```bash
make airflow_setup
```

Finally, let's run the two Airflow instances with environment variables set:

In one shell run:

```bash
make warehouse_airflow_run
```

In a separate shell, run:

```bash
make metrics_airflow_run
```

This will run two Airflow Web UIs, one for each Airflow instance. You should now be able to access the warehouse Airflow UI at `http://localhost:8081`, with the default username and password set to `admin`.

You should be able to see the `load_customers` DAG in the Airflow UI.

![load_customers DAG](/images/integrations/airlift/load_customers.png)

Similarly, you should be able to access the metrics Airflow UI at `http://localhost:8082`, with the default username and password set to `admin`.

You should be able to see the `customer_metrics` DAG in the Airflow UI.

![customer_metrics DAG](/images/integrations/airlift/customer_metrics.png)

## Next steps

In the next section, we'll add asset representations of our DAGs, and set up lineage across both Airflow instances. Follow along [here](observe).
