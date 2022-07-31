from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="assets_dbt_python",
        packages=find_packages(exclude=["assets_dbt_python_tests"]),
        package_data={"assets_dbt_python": ["dbt_project/*"]},
        install_requires=[
            "dagster",
            "dagit",
            "dagster-dbt",
            "pandas",
            "numpy",
            "scipy",
            "dbt-core",
            "dbt-duckdb",
        ],
        extras_require={"tests": ["mypy", "pylint", "pytest"]},
    )
