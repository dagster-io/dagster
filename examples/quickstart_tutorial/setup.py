from setuptools import find_packages, setup

setup(
    name="quickstart_tutorial",
    packages=find_packages(exclude=["quickstart_tutorial_tests"]),
    install_requires=["dagster", "dagster-cloud"],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
