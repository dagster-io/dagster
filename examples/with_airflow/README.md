# Using Dagster with Airflow Example

Dagster is a fully-featured orchestrator and does not require a system like Airflow to deploy, execute, or schedule jobs. The main scenarios for using Dagster with Airflow are:
- You have an existing Airflow setup that's too difficult to migrate away from, but you want to use Dagster for local development.
- You want to migrate from Airflow to Dagster in an incremental fashion.

View this example in the Dagster docs at https://docs.dagster.io/integrations/airflow.


## Getting started

```bash
dagster project from-example --name my-dagster-project --example with_airflow
```