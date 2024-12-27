from setuptools import find_packages, setup

setup(
    name="mwaa-example",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-webserver",
        "dagster-airlift[core,mwaa]",
    ],
    extras_require={"test": ["pytest"]},
)
