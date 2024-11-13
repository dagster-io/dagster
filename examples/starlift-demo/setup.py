from setuptools import find_packages, setup

setup(
    name="dbt-example",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-webserver",
        "dagster-airlift[dbt,core,in-airflow]",
        "dagster-dlift",
        "dbt-duckdb",
        "pandas",
    ],
    extras_require={"test": ["pytest"]},
)
