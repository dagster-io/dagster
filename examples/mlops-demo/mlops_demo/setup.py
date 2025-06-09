from setuptools import find_packages, setup

setup(
    name="mlops_demo",
    packages=find_packages(exclude=["mlops_demo_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud"
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
