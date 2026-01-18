from setuptools import find_packages, setup

setup(
    name="with_great_expectations",
    packages=find_packages(exclude=["with_great_expectations_tests"]),
    install_requires=[
        "dagster",
        "dagster-ge",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
