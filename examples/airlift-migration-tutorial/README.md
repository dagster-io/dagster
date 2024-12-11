## Airlift Tutorial Code

This repo is the code that the Airlift tutorial is based off of. Follow along on the main docs site [here](https://docs.dagster.io/integrations/airlift/tutorial/overview).
This example demonstrates how to migrate an Airflow DAG to Dagster using the `dagster-airlift` package. It contains code examples of how to peer, observe, and migrate assets from an Airflow DAG to Dagster.

## Example Structure

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
