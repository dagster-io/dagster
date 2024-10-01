---
title: "Lesson 2: Set up the dbt project"
module: 'dagster_dbt'
lesson: '2'
---

# Set up the dbt project

Next, you’ll notice that there is a dbt project called `analytics` in the repository you cloned. Throughout the duration of this module, you’ll add new dbt models and see them reflected in Dagster.

1. Navigate into the directory by running:
    
    ```bash
    cd analytics
    ```
    
2. Next, install dbt package dependencies by running:
    
    ```bash
    dbt deps
    ```
    
3. In a file explorer or IDE, open the `analytics` directory. You should see the following files, which are the models we’ll use to get started:

    - `models/sources/raw_taxis.yml`
    - `models/staging/staging.yml`
    - `models/staging/stg_trips.sql`
    - `models/staging/stg_zones.sql`