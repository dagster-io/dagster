from setuptools import find_packages, setup

setup(
    name="gcp-test-proj",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-webserver",
        "dagster-gcp",
    ],
    extras_require={"test": ["pytest"]},
)
