from setuptools import find_packages, setup

setup(
    name="starlift-demo",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-webserver",
        "dagster-airlift[core,in-airflow]",
        "dagster-dbt",
        "dbt-duckdb",
        "pandas",
        "apache-airflow<3.0.0",
    ],
    extras_require={"test": ["pytest"]},
)
