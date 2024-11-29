This example shows how you can use Airlift to migrate + refactor at once.

Project structure:
```plaintext
├── Makefile
├── README.md
├── airflow-codebase - a model of the "current" airflow codebase
│   ├── airflow_dags
│   │   ├── proxied_state - stores state of whether each task should be "proxied to Dagster" for execution.
│   │   ├── dbt_and_ecs.py
│   │   └── scraping_and_dbt.py
│   ├── airflow_shared - shared code for Airflow project. Contains custom operators.
│   ├── customers-dbt - a dbt project containing "customers" related models, used in one of the dags.
│   ├── orders-dbt - a dbt project containing "orders" related models, used in another of the dags.
├── dagster-codebase - a model of the dagster codebase as you're migrating each task with Airlift.
│   ├── adhoc-location - corresponds to the ecs task operator in Airflow - to run isolated environments, we'll instead use uv venvs.
│   │   ├── adhoc
│   │   │   ├── __init__.py
│   │   │   ├── defs.py
│   │   │   ├── req_files
│   │   │   │   └── my_req_file.txt
│   │   │   └── scripts
│   │   │       └── my_script.py
│   │   └── setup.py
│   ├── scraping-location - contains website scraping code.
│   │   ├── README.md
│   │   ├── scraping
│   │   │   ├── __init__.py
│   │   │   └── defs.py
│   │   └── setup.py
│   ├── sdf-location - contains code running the sdf project.
│   │   ├── my_sdf
│   │   │   └── defs.py
│   │   └── setup.py
│   ├── sdf-project - global sdf project containing all your models (comprises both customers-dbt and orders-dbt)
│   │   ├── models
│   │   │   ├── raw
│   │   │   │   └── seeds.sdf.yml
│   │   │   └── staging
│   │   │       ├── stg_customers.sql
│   │   │       └── stg_orders.sql
│   │   ├── seeds
│   │   │   ├── raw_customers.csv
│   │   │   └── raw_orders.csv
```
The example shows having two dags, with similar structure but disconnected from each other.
- The first dag 
    - scrapes data from an API
    - materializes a set of dbt models using a BashOperator.
- The second dag
    - materializes a set of dbt models using a BashOperator (waiting for seeds to exist using a sensor).
    - performs some arbitrary computation in an Ecs container

We're going to use Dagster to modernize this workflow and escape from dependency hell. Here are the steps:
- We'll create a code location for each separate "task type";
    - An "sdf" code locatin to replace our dbt code location
    - A "scraping" code location to replace our scraper usage
    - A code location that allows us to build arbitrary python packages and execute them (this is what we'll use to execute the custom munging)
- We're going to copy over these two dbt projects into a single sdf project
- We're going to create two separate computable assets that correspond to our two different task to correspond to our different scheduling needs.
- We'll create two separate code locations, for the other tasks we're performing.

Why use Airlift here?
- Airlift provides you tools to migrate in a more efficient fashion, and effectively "pause" the migration if needed.
- Without Airlift, the most incremental process you could enable is to individually migrate on a DAG-by-DAG basis. But this is going to require you to build out all of these code locations at once, just for a single dag, and also encounter basically every dagster concept at once. It's also much more risky, because you have many more individual points of failure - one per task. The alternative of just migrating everything wholesale and then flipping the switch is obviously inadvisable. This also has way more context switching - you have to switch between contexts and migration processes for every DAG, and while the process will get easier, context switching adds up. Also, what do you do if you have to pause in the middle of migrating a dag? How do you roll back? There's no direct equivalent to your dag in dagster (unless you build a job per dag, which is inadvisable because it's not best practice, so rollback becomes much more complicated).
- In comparison, Airlift is going to allow you to build things up on a per-technology basis. You can for example, focus first on building out the sdf code location. You build that initial factory function, then follow the _same exact simple process_ for every single dbt task. Becomes highly automatic. And because the process is the same, you build up confidence, and can do this process for every dag. If you need to pause in the middle, it still leaves you in a good state, because all the intermediate code is still in production. It also makes the rollback process very clear. You just flip the switch on a single task. You can then follow this for every technology, and eventually decomission the dag. It also allows you to report on the status of the migration very easily, you are able to understand exactly how many dags / tasks have been migrated.
