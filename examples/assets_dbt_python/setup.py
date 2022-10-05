from setuptools import find_packages, setup

setup(
    name="assets_dbt_python",
    packages=find_packages(exclude=["assets_dbt_python_tests"]),
    package_data={"assets_dbt_python": ["dbt_project/*"]},
    install_requires=[
        "dagster",
        "dagster-dbt",
        "pandas",
        "numpy",
        "scipy",
        "dbt-core",
        "dbt-duckdb",
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
