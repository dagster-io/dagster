from setuptools import find_packages, setup

setup(
    name="tutorial",
    packages=find_packages(exclude=["tutorial_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud",
        "Faker==18.4.0",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
