from setuptools import find_packages, setup

setup(
    name="with_airflow",
    packages=find_packages(exclude=["with_airflow_tests"]),
    install_requires=[
        "dagster",
        "dagster_airflow",
        "apache-airflow",
        # for the kubernetes operator
        "apache-airflow-providers-cncf-kubernetes>=4.4.0",
        "apache-airflow-providers-docker>=3.1.0",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
