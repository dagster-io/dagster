from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="assets_modern_data_stack",
        packages=find_packages(exclude=["assets_modern_data_stack_tests"]),
        package_data={"assets_modern_data_stack": ["dbt_project/*"]},
        install_requires=[
            "dagster",
            "dagster-airbyte",
            "dagster-dbt",
            "dagster-postgres",
            "pandas",
            "numpy",
            "scipy",
            "dbt-core",
            "dbt-postgres",
        ],
        extras_require={"dev": ["dagit", "pytest"]},
    )
