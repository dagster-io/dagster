from setuptools import find_packages, setup

setup(
    name="pipeline2",
    packages=find_packages(exclude=["pipeline2_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud"
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
