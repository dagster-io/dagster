from setuptools import find_packages, setup

setup(
    name="dagster-dbt-cloud-kitchen-sink",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-webserver",
        "dagster-dbt",
        "dbt-core>=1.4.0",
    ],
    extras_require={"test": ["pytest"]},
)
