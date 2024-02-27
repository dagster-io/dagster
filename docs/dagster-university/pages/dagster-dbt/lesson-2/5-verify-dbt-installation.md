---
title: "Lesson 2: Verify dbt installation"
module: 'dagster_dbt'
lesson: '2'
---

# Verify dbt installation

Before continuing, let’s run the dbt project from the command line to confirm that everything is configured correctly.

From the `analytics`  directory, run the following command:

```bash
dbt build
```

The two staging models should materialize successfully and pass their tests:

```bash
19:56:02  dbt build
19:56:03  Running with dbt=1.7.8
19:56:05  Registered adapter: duckdb=1.7.1
19:56:05  Unable to do partial parsing because saved manifest not found. Starting full parse.
19:56:07  Found 2 models, 2 tests, 2 sources, 0 exposures, 0 metrics, 505 macros, 0 groups, 0 semantic models
19:56:07  
19:56:07  Concurrency: 1 threads (target='dev')
19:56:07  
19:56:07  1 of 4 START sql table model main.stg_trips .................................... [RUN]
19:56:09  1 of 4 OK created sql table model main.stg_trips ............................... [OK in 1.53s]
19:56:09  2 of 4 START sql table model main.stg_zones .................................... [RUN]
19:56:09  2 of 4 OK created sql table model main.stg_zones ............................... [OK in 0.07s]
19:56:09  3 of 4 START test accepted_values_stg_zones_borough__Manhattan__Bronx__Brooklyn__Queens__Staten_Island__EWR  [RUN]
19:56:09  3 of 4 PASS accepted_values_stg_zones_borough__Manhattan__Bronx__Brooklyn__Queens__Staten_Island__EWR  [PASS in 0.06s]
19:56:09  4 of 4 START test not_null_stg_zones_zone_id ................................... [RUN]
19:56:09  4 of 4 PASS not_null_stg_zones_zone_id ......................................... [PASS in 0.04s]
19:56:09  
19:56:09  Finished running 2 table models, 2 tests in 0 hours 0 minutes and 1.95 seconds (1.95s).
19:56:09  
19:56:09  Completed successfully
19:56:09  
19:56:09  Done. PASS=4 WARN=0 ERROR=0 SKIP=0 TOTAL=4
```