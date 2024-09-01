from pathlib import Path

from setuptools import find_packages, setup

airflow_dep_list = [
    "apache-airflow>=2.0.0,<2.8",
    # Flask-session 0.6 is incompatible with certain airflow-provided test
    # utilities.
    "flask-session<0.6.0",
    "connexion<3.0.0",  # https://github.com/apache/airflow/issues/35234
    "pendulum>=2.0.0,<3.0.0",
]

setup(
    name="dagster-airlift",
    version="0.0.14",
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Tooling to assist with migrating from Airflow to Dagster.",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    url=(
        "https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/"
        "dagster-airlift"
    ),
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_airlift_tests*", "examples*"]),
    extras_require={
        "core": [
            "dagster",
        ],
        "in-airflow": airflow_dep_list,
        "mwaa": ["boto3"],
        "dbt": ["dagster-dbt"],
        "test": ["pytest", "dagster-dbt", "dbt-duckdb", "boto3", "dagster-webserver"],
    },
    zip_safe=False,
)
