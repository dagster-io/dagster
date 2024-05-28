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
    ],
    extras_require={
        "dev": [
            "dagster-webserver",
            "pytest",
        ],
        "test": [
            # cant build psycopg2 in buildkite
            # something about the 1.8.0 dependency setup to avoid psycopg2-binary on linux
            # seems to prevent that dependency from being used even if explicitly added
            "dbt-postgres<1.8.0"
        ],
    },
)
