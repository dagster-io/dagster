---
title: "Lesson 2: Set up the dbt project"
module: 'dagster_dbt'
lesson: '2'
---

# Set up the dbt project

Next, you’ll create a dbt project to work with Dagster. During the course of this module, you’ll add new dbt models and see them reflected in Dagster.

To get you started, we made a dbt project with a couple of staging models. From within the `project-dagster-university`  directory, clone this dbt project by performing the following steps.

1. In the command line, run:
    
    ```bash
    git clone TODO analytics 
    ```
    
2. This will create a new directory called `analytics`. Navigate into the directory by running:
    
    ```bash
    cd analytics
    ```
    
3. Next, install dbt package dependencies by running:
    
    ```bash
    dbt deps
    ```
    
4. In a file explorer or IDE, open the `analytics` directory. You should see the following files, which are the models we’ll use to get started:

    - `models/sources/raw_taxis.yml`
    - `models/staging/staging.yml`
    - `models/staging/stg_trips.yml`
    - `models/staging/stg_zones.yml`