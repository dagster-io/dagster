from setuptools import setup, find_packages

setup(
    name="my-dagster-project",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "dagster>=1.11.2",
        "dagster-docker",
        "loguru",
    ],
)
