"""Main Dagster Definitions for data quality patterns.

This project demonstrates data quality validation across all 7 dimensions:
1. Accuracy - Data correctly represents real-world entities
2. Completeness - All required data is present
3. Consistency - Data is uniform across datasets
4. Timeliness - Data is up-to-date (freshness policies on assets)
5. Validity - Data conforms to formats and rules
6. Uniqueness - No unwanted duplicates
7. Integrity - Relationships between data are maintained

Check Types:
- Native Python asset checks
- Great Expectations checks
- dbt tests as asset checks
- Freshness policies for timeliness monitoring
"""

import dagster as dg
from dagster_dbt import DbtCliResource
from dagster_duckdb import DuckDBResource

import data_quality_patterns.defs as defs_module
from data_quality_patterns.project import DUCKDB_PATH, dbt_project


@dg.definitions
def defs():
    return dg.Definitions.merge(
        dg.components.load_defs(defs_module),
        dg.Definitions(
            resources={
                "duckdb": DuckDBResource(database=DUCKDB_PATH),
                "dbt": DbtCliResource(project_dir=dbt_project),
            },
        ),
    )
