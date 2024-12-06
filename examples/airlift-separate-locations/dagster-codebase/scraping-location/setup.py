from setuptools import find_packages, setup

setup(
    name="scraping",
    packages=find_packages(),
    install_requires=[
        "dagster-airlift[core]",
        "dagster",
        "selenium",
    ],
    extras_require={"test": ["pytest"]},
)
