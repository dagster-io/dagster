from setuptools import find_packages, setup

setup(
    name="azure-test-proj",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-webserver",
        "dagster-azure",
    ],
    extras_require={"test": ["pytest"]},
)
