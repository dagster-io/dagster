from setuptools import find_packages, setup

setup(
    name="use_case_repository",
    packages=find_packages(exclude=["use_case_repository_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud",
        "boto3",
        "pandas",
        "matplotlib",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
