from setuptools import find_packages, setup

setup(
    name="quickstart_etl",
    packages=find_packages(exclude=["quickstart_etl_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud",
        "boto3",
        "pandas",
        "matplotlib",
        # highlight-start
        "soda @ https://pypi.cloud.soda.io/packages/soda-1.6.2.tar.gz",
        "soda-snowflake @ https://pypi.cloud.soda.io/packages/soda_snowflake-1.6.2.tar.gz",
        # highlight-end
    ],
    extras_require={
        "dev": [
            "dagster-webserver",
            "dagster-dg-cli",
        ]
    },
)
