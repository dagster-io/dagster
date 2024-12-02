## Airlift Federation Tutorial Code

This is the code that the Airlift federation tutorial is based off of.

This example demonstrates how to use the `dagster-airlift` package to unify multiple Airflow instances into Dagster as a single control plane, and then federate execution between those Airflow instances.

## Example Structure

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
