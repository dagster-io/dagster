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

The two staging models should materialize successfully and pass their tests.

<!-- TODO: should we add logs or something about potential errors here? -->