from setuptools import find_packages, setup

setup(
    name="assets_modern_data_stack",
    packages=find_packages(exclude=["assets_modern_data_stack_tests"]),
    package_data={"assets_modern_data_stack": ["../dbt_project/*", "../dbt_project/*/*"]},
    install_requires=[
        "dagster",
        "dagster-cloud",
        "boto3",
        "dagster-airbyte",
        "dagster-dbt",
        "dagster-postgres",
        "pandas",
        "numpy",
        "scipy",
        "dbt-core",
        "dbt-postgres",
        "packaging<22.0",  # match dbt-core's requirement to workaround a resolution issue
        "croniter<1.4.0",  # https://github.com/dagster-io/dagster/pull/14811
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
