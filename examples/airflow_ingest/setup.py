from setuptools import find_packages, setup

setup(
    name="airflow_ingest",
    version="0+dev",
    author_email="hello@elementl.com",
    packages=find_packages(exclude=["airflow_ingest_tests*"]),
    include_package_data=True,
    install_requires=[
        "dagster",
        "dagster-airflow",
        "dagit",
        # See https://github.com/dagster-io/dagster/issues/2701
        "apache-airflow==1.10.10",
    ],
    python_requires=">=3.6,<=3.8",
    author="Elementl",
    license="Apache-2.0",
    description="Dagster example of ingesting data with airflow",
    url="https://github.com/dagster-io/dagster/tree/master/examples/airflow_ingest",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
