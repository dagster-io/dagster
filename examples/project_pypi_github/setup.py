from setuptools import find_packages, setup

setup(
    name="dagster_pypi",
    packages=find_packages(exclude=["dagster_pypi_tests"]),
    install_requires=[
        "dagster~=1.3",
        "dagster-cloud",
        "dagster-dbt~=0.19",
        "dagster-duckdb-pandas~=0.18",
        "dagster-gcp~=0.18",
        "dagster-gcp-pandas~=0.18",
        "dagster-hex~=0.1",
        "dagster-pandas~=0.18",
        "dbt-bigquery~=1.4",
        "dbt-duckdb~=1.4",
        "google-cloud-bigquery~=3.9",
        "psycopg2-binary~=2.9",

    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
