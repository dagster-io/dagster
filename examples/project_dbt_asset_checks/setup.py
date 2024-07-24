import glob

from setuptools import find_packages, setup

setup(
    name="project_dbt_asset_checks",
    packages=find_packages(exclude=["project_dbt_asset_checks_tests"]),
    # package data paths are relative to the package key
    package_data={
        "project_dbt_asset_checks": [
            "../" + path for path in glob.glob("dbt_project/**", recursive=True)
        ]
    },
    install_requires=[
        "dagster",
        "dagster-dbt",
        "dbt-duckdb",
        "dagster-duckdb",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
