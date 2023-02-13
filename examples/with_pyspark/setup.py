from setuptools import find_packages, setup

setup(
    name="with_pyspark",
    packages=find_packages(exclude=["with_pyspark_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud",
        "dagster-spark",
        "dagster-pyspark",
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
