from setuptools import find_packages, setup

setup(
    name="project_atproto_dashboard",
    packages=find_packages(exclude=["project_atproto_dashboard_tests"]),
    install_requires=[
        "atproto",
        "dagster",
        "dagster-dg-cli",
        "dagster-aws",
        "dagster-dbt",
        "dagster-duckdb",
        "dagster-powerbi",
        "dagster-webserver",
        "dbt-duckdb",
        "tenacity",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest", "ruff"]},
)
