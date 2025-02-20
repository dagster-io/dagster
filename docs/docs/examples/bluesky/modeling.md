---
title: Modeling data
description: Modeling data in dbt and DuckDB
last_update:
  author: Dennis Hume
sidebar_position: 40
---

After running the ingestion assets, we will have all the data we need in R2 to start modeling. We will use [dbt](https://www.getdbt.com/) to handle our transformation logic and [DuckDB](https://duckdb.org/) as our query engine. We will combine both of these together and add them into our Dagster asset graph.

The first thing to do is set up our dbt project. We will configure the connection details for the R2 bucket and the DuckDB database in the `profiles.yml` file. We will define two profiles, each with their own schema and path for our dev and production environments.

<CodeExample path="docs_projects/project_atproto_dashboard/dbt_project/profiles.yml" language="yaml" startAfter="start_profile" endBefore="end_profile"/>

Next we can define the `sources.yml` which will be the foundation for our dbt models. We can use the DuckDB function [read_ndjson_objects](https://duckdb.org/docs/data/json/loading_json.html#functions-for-reading-json-objects) to retrieve all the data in our specific R2 object paths. Even though all the data exists within the same R2 bucket, it can still be mapped into individual tables in DuckDB.

<CodeExample path="docs_projects/project_atproto_dashboard/dbt_project/models/sources.yml" language="yaml" startAfter="start_sources" endBefore="end_sources"/>

| DuckDB Table | R2 Path |
| --- | --- |
| `{profiles schema}.actor_feed_snapshot` | `r2://dagster-demo/atproto_actor_feed_snapshot/` |
| `{profiles schema}.starter_pack_snapshot` | `r2://dagster-demo/atproto_starter_pack_snapshot/` |

## Modeling

With dbt configured to read our JSON data, we can start to build the models. We will follow dbt conventions and begin with staging models that map to the tables defined in the `sources.yml`. These will be models that extract all the information.

<CodeExample path="docs_projects/project_atproto_dashboard/dbt_project/models/staging/stg_feed_snapshots.sql" language="sql" startAfter="start_stg_feed_snapshots" endBefore="end_stg_feed_snapshots"/>

Within the dbt project the `analysis` directory builds out the rest of the models where more complex metrics such as top daily posts are calculated. For metrics such as latest feeds, we can also leverage how we partitioned the data within our R2 bucket during ingestion to ensure we are using the most up to date posts.

<CodeExample path="docs_projects/project_atproto_dashboard/dbt_project/models/analysis/latest_feed.sql" language="sql" startAfter="start_latest_feed_cte" endBefore="end_latest_feed_cte"/>

### dbt assets

Moving back into Dagster, there is not too much we need to do to turn the dbt models into assets. Dagster can parse a dbt project and generate all the assets by using a path to the project directory.

<CodeExample path="docs_projects/project_atproto_dashboard/project_atproto_dashboard/modeling/definitions.py" language="python" startAfter="start_dbt_project" endBefore="end_dbt_project"/>

We will use the `DagsterDbtTranslator` to map our ingestion assets that bring in the Bluesky data to the tables we defined in the `sources.yml`. This will ensure that everything exists as part of the same DAG and lineage within Dagster. Next we will combine the translator and dbt project to generate our Dagster assets. 

<CodeExample path="docs_projects/project_atproto_dashboard/project_atproto_dashboard/modeling/definitions.py" language="python" startAfter="start_dbt_assets" endBefore="end_dbt_assets"/>

Like the ingestion layer, we will create a definition specific to dbt and modeling which we will combine with the other layers of our project.

There is one final layer to add to make a full end-to-end analytics pipeline. Next we will add in the dashboarding.

## Next steps

- Continue this example with [dashboard](dashboard)