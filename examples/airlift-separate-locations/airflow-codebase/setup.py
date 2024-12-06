from setuptools import find_packages, setup

setup(
    name="airflow-shared",
    packages=find_packages(),
    install_requires=[
        "dagster-airlift[tutorial]",
        "dagster-webserver",
        # Need this for dbt models
        "dbt",
        "dbt-duckdb",
        # Need this for scrapers
        "selenium",
        # Need this for aws / ecs
        "boto3",
    ],
    extras_require={"test": ["pytest"]},
)
