# dagster-airlift

The goal of Airlift is to accelerate, lower the cost, and reduce the risk of migrating to Dagster from Airflow. The tool allows you to:

- Visualize and observe your existing Airflow DAGs within Dagster with no code changes in Airflow and few lines of code in your Dagster deployment.
- Model the assets produced by your Airflow instance prior to migration in Dagster (e.g. make your dbt models appear in Dagster while they are orchestrated by Airflow).
- Enable incremental migration of your Airflow tasks one-by-one, in any order. While the migration is happening, your Airflow DAG structures remain untouched from the standpoint of the observer.

Tl;dr With Airlift, Dagster first becomes your “single pane of glass” for all orchestration and then acts as a toolkit to accelerate a low-risk migration process. Another design partner we are talking to describes this as “changing the oil while driving the car” which I think is a memorable analogy.

With this we imagine an accelerated, low-risk, incremental process with reduced coordination costs:

- You can migrate your Airflow tasks to Dagster in any order
- You can easily “rollback” the migration on a per-task basis if there are problems or bugs

Since your Airflow DAG structure and execution history largely stays the same during the migration, any operational tooling continues to work as is. Anyone accustomed to viewing the Airflow UI will not have to be aware of the migration in most cases.

Dagster is the “source of truth” for the state of migration as you can tell what assets and tasks have been fully migrated and which ones have not.

This will greatly accelerate the migration because you can migrate tasks in parallel, in any order, with high trust, and do so aggressively because rolling back is easy, all within an orderly, observed, tool-assisted process.

## Trying out airlift

See the peering process in action by trying out the example:

- [Airflow-Dagster Peering with DBT](examples/peering-with-dbt)
