from setuptools import find_packages, setup

setup(
    name="peered-mwaa",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-webserver",
        "dagster-airlift[core]",
    ],
    extras_require={"test": ["pytest"]},
)
