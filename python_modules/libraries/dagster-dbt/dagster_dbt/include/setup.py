from setuptools import find_packages, setup

setup(
    name="dbt_scaffold",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-cloud",
        "dagster-dbt",
        "dbt-core>=1.4.0",
    ],
    extras_require={"dev": ["dagit"]},
)
