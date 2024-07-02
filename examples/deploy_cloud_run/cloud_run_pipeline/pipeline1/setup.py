from setuptools import find_packages, setup

setup(
    name="pipeline1",
    packages=find_packages(exclude=["pipeline1_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud"
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
