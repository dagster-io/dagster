# Airlift

Airlift is a toolkit for observing Airflow instances from within Dagster and for accelerating the migration of Airflow DAGs to Dagster assets.

## Goals

- Observe Airflow DAGs and their execution history with no changes to Airflow code
- Model and observe assets orchestrated by Airflow with no changes to Airflow code
- Enable a migration process that
  - Can be done task-by-task in any order with minimal coordination
  - Has task-by-task rollback to reduce risk
  - That retains Airflow DAG structure and execution history during the migration

## Process

- **Peer**
  - Observe an Airflow instance from within a Dagster Deployment via the Airflow REST API.
  - This loads every Airflow DAG as an asset definition and creates a sensor that polls Airflow for execution history.
- **Observe**
  - Add a mapping that maps the Airflow DAG and task id to a basket of definitions that you want to observe. (e.g. render the full lineage the dbt models an Airflow task orchestrates)
  - The sensor used for peering also polls for task execution history, and adds materializations to an observed asset when its corresponding task successfully executes
- **Migrate**
  - Selectively move execution of Airflow tasks to Dagster Software Defined Assets

## Compatibility

### REST API Availability

Airlift depends on the the availability of Airflow’s REST API. Airflow’s REST API was made stable in its 2.0 release (Dec 2020) and was introduced experimentally in 1.10 in August 2018. Currently Airflow requires the availability of the REST API.

- **OSS:** Stable as of 2.00
- **MWAA**
  - Note: only available in Airflow 2.4.3 or later on MWAA.
- **Cloud Composer:** No limitations as far as we know.
- **Astronomer:** No limitations as far as we know.

# Tutorial

We've provided a tutorial to help get you started with airlift tooling and process, which can be found [here](https://github.com/dagster-io/airlift-migration-tutorial).
