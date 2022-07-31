from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="assets_modern_data_stack",
        packages=find_packages(exclude=["assets_modern_data_stack_tests"]),
        package_data={"assets_modern_data_stack": ["mds_dbt/*"]},
        install_requires=[
            "dagster",
            "dagit",
            "dagster-airbyte",
            "dagster-dbt",
            "dagster-postgres",
            "pandas",
            "numpy",
            "scipy",
            "dbt-core",
            "dbt-postgres",
        ],
    )
