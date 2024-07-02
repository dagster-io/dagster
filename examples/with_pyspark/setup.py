from setuptools import setup, find_packages

setup(
    name="with_pyspark",
    packages=find_packages(exclude=["with_pyspark_tests"]),
    install_requires=[
        "dagster",
        "dagster-spark",
        "dagster-pyspark",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
