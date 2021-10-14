from setuptools import setup

setup(
    name="dbt_example",
    version="dev",
    author_email="hello@elementl.com",
    packages=["dbt_example"],
    include_package_data=True,
    install_requires=[
        "dagster",
        "dagit",
        "dagster-dbt",
        "dagster-pandas",
        "dagster-postgres",
        "dagster-slack",
        "dagstermill",
        "dbt",
    ],
    author="Elementl",
    license="Apache-2.0",
    description="Dagster example for integrating with dbt.",
    url="https://github.com/dagster-io/dagster/tree/master/examples/dbt_examples",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
