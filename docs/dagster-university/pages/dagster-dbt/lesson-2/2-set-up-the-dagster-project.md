---
title: "Lesson 2: Set up the Dagster project"
module: 'dagster_dbt'
lesson: '2'
---

# Set up the Dagster project

After downloading the Dagster University project, you’ll need to make a few changes to finish setting things up. 

First, you’ll add a few additional dependencies to the project: 

- `dagster-dbt` - Dagster’s integration library for dbt. This will also install `dbt-core` as a dependency.
- `dbt-duckdb` - A library for using dbt with DuckDB, which we’ll use to store the dbt models we create

Locate the `setup.py` file in the root of the Dagster University project. Open the file and replace it with the following:

```python
from setuptools import find_packages, setup

setup(
    name="dagster_university",
    packages=find_packages(exclude=["dagster_university_tests"]),
    install_requires=[
        "dagster==1.9.*",
        "dagster-cloud",
        "dagster-duckdb",
        "dagster-dbt",
        "dbt-duckdb",
        "geopandas",
        "pandas[parquet]",
        "matplotlib",
        "shapely",
        "smart_open[s3]",
        "s3fs",
        "smart_open",
        "boto3",
        "pyarrow",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
```

{% callout %}
💡 **Heads up!** We strongly recommend installing the project dependencies inside a Python virtual environment. If you need a primer on virtual environments, including creating and activating one, check out this [blog post](https://dagster.io/blog/python-packages-primer-2).
{% /callout %}

Then, run the following in the command line to rename the `.env.example`  file and install the dependencies:

```bash
cd dagster-and-dbt
cp .env.example .env
pip install -e ".[dev]"
```

The `e` flag installs the project in editable mode so you can modify existing Dagster assets without having to reload the code location. This allows you to shorten the time it takes to test a change. However, you’ll need to reload the code location in the Dagster UI when adding new assets or installing additional dependencies.

To confirm everything works:

1. Run `dagster dev`  from the directory.
2. Navigate to the Dagster UI ([`http://localhost:3000`](http://localhost:3000/)) in your browser.
3. Open the asset graph by clicking **Assets > View global asset lineage** and confirm the asset graph you see matches the graph below.

   ![The Asset Graph in the Dagster UI](/images/dagster-dbt/lesson-2/asset-graph.png)

4. Let's confirm that you can materialize these assets by:
   1. Navigating to **Overview > Jobs**
   2. Clicking on the `trip_update_job` job and then **Materialize all...**. 
   3. When prompted to select a partition, materialize the most recent one (`2023-03-01`). It will start a run/backfill and your assets should materialize successfully.
