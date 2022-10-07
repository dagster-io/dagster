from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="assets_smoke_test",
        packages=find_packages(exclude=["assets_smoke_test_tests"]),
        package_data={"assets_smoke_test": ["dbt_project/*"]},
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
