from setuptools import setup, find_packages

setup(
    name="assets_dynamic_partitions",
    packages=find_packages(exclude=["assets_dynamic_partitions_tests"]),
    install_requires=[
        "dagster",
        "dagster-duckdb-pandas",
        "requests",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
