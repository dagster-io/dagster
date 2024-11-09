from setuptools import find_packages, setup

setup(
    name="kitchen-sink",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-webserver",
        "dagster-airlift[core,in-airflow]",
    ],
    extras_require={"test": ["pytest"]},
)
