from setuptools import find_packages, setup

setup(
    name="etl_tutorial",
    packages=find_packages(exclude=["etl_tutorial_tests"]),
    install_requires=["dagster", "dagster-cloud", "duckdb"],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
