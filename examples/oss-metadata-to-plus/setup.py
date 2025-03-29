from setuptools import find_packages, setup

setup(
    name="metadata_to_plus",
    packages=find_packages(exclude=["metadata_to_plus_tests"]),
    install_requires=["dagster", "dagster-cloud"],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
