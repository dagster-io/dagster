from setuptools import find_packages, setup

setup(
    name="tutorial",
    packages=find_packages(exclude=["tutorial_tests"]),
    install_requires=[
        "dagster",
        "dagster_duckdb_pandas",
        "dagster_duckdb",
        "dagster-cloud",
        "Faker==18.4.0",
        "matplotlib",
        "pandas",
        "requests",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
