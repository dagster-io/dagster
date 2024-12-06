from setuptools import find_packages, setup

setup(
    name="my_sdf",
    packages=find_packages(),
    install_requires=[
        "dagster-airlift[core]",
        "dagster",
        "sdf-cli",
    ],
    extras_require={"test": ["pytest"]},
)
