from setuptools import find_packages, setup

setup(
    name="dagster_university",
    packages=find_packages(exclude=["dagster_university_tests"]),
    install_requires=[
        "dagster==1.3.*",
        "dagster-cloud",
        "dagster-dbt",
        "dagster-duckdb",
        "dagster-gcp",
        "dbt-duckdb",
        "geopandas",
        "kaleido",
        "pandas",
        "plotly",
        "psycopg2-binary",
        "shapely"
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
