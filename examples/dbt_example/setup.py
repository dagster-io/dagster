from setuptools import setup

setup(
    name="dbt_example",
    version="0+dev",
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
        "dbt-core",
        "dbt-postgres",
    ],
    python_requires=">=3.7,<=3.9",
    author="Elementl",
    license="Apache-2.0",
    description="Dagster example for integrating with dbt.",
    url="https://github.com/dagster-io/dagster/tree/master/examples/dbt_examples",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
