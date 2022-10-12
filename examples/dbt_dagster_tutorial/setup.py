from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="dbt_dagster_tutorial",
        packages=find_packages(),
        install_requires=[
            "dagster",
            "dagster-dbt",
            "pandas",
            "dbt-core",
            "dbt-duckdb",
            "dagster-duckdb",
            "dagster-duckdb-pandas",
        ],
        extras_require={"dev": ["dagit", "pytest"]},
    )
