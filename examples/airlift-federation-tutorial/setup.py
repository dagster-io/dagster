from setuptools import find_packages, setup

setup(
    name="airlift-federation-tutorial",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-webserver",
        "dagster-airlift[dbt,core]",
    ],
    extras_require={"test": ["pytest"]},
)
