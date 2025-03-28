from setuptools import find_packages, setup

setup(
    name="quickstart_etl",
    packages=find_packages(exclude=["quickstart_etl_tests"]),
    install_requires=[
        "dagster",
        # highlight-start
        # when possible, add additional dependencies in setup.py
        "boto3",
        "pandas",
        "matplotlib",
        # highlight-end
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
