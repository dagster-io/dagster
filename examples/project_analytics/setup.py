from setuptools import find_packages, setup

setup(
    name="dagster_pypi",
    packages=find_packages(exclude=["dagster_pypi_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud",
        "dagster-dbt",
        "dagster-duckdb-pandas",
        "dagster-gcp",
        "dagster-gcp-pandas",
        "dagster-hex",
        "dagster-pandas",
        "dbt-bigquery",
        "dbt-duckdb",
        "google-cloud-bigquery",
        "psycopg2-binary",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
