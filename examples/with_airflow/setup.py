from setuptools import find_packages, setup

setup(
    name="with_airflow",
    packages=find_packages(exclude=["with_airflow_tests"]),
    install_requires=[
        "dagster",
        "dagster_airflow",
        "apache-airflow==2.3.0",
        # pin jinja2 to version compatible with dagit and airflow
        "jinja2==3.0.3",
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
