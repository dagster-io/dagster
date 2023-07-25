from setuptools import find_packages, setup

setup(
    name="tutorial_dbt_dagster_v2",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-dbt",
        "dbt-core>=1.4.0",
        "dbt-duckdb",
    ],
    extras_require={"dev": ["dagster-webserver"]},
)
