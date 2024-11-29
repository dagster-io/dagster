from setuptools import find_packages, setup

setup(
    name="adhoc",
    packages=find_packages(),
    install_requires=[
        "dagster-airlift[core]",
        "dagster",
    ],
    extras_require={"test": ["pytest"]},
)
