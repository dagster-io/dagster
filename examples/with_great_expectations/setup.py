from setuptools import find_packages, setup

setup(
    name="with_great_expectations",
    packages=find_packages(exclude=["with_great_expectations_tests"]),
    install_requires=[
        "dagster",
        "dagster-ge",
        "great_expectations>=0.14.12",  # pinned because pip is using the cached wheel for 0.13.14
        # https://github.com/great-expectations/great_expectations/issues/7990
        "typing_extensions<4.6.0",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
