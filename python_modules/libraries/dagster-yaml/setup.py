from setuptools import find_packages, setup

setup(
    name="dagster_yaml",
    packages=find_packages(exclude=["dagster_yaml_tests"]),
    install_requires=[
        "dagster",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
