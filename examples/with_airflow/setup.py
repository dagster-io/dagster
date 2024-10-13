from setuptools import find_packages, setup

setup(
    name="with_airflow",
    packages=find_packages(exclude=["with_airflow_tests"]),
    install_requires=[
        "dagster",
        "dagster_airflow",
        "apache-airflow",
        # Flask-session 0.6 is incompatible with certain airflow-provided test
        # utilities.
        "flask-session<0.6.0",
        # for the kubernetes operator
        "apache-airflow-providers-cncf-kubernetes>=4.4.0",
        "apache-airflow-providers-docker>=3.1.0",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
