from setuptools import find_packages, setup

setup(
    name="assets_smoke_test",
    packages=find_packages(exclude=["assets_smoke_test_tests"]),
    package_data={"assets_smoke_test": ["dbt_project/*"]},
    install_requires=[
        "dagster",
        "dagster-pandas",
        "dagster-dbt",
        "pandas",
        "dbt-core",
        "dbt-snowflake",
        "dagster-snowflake",
        "dagster-snowflake-pandas",
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
