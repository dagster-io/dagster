from setuptools import find_packages, setup

setup(
    name="iris_analysis",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-cloud",
        "pandas",
    ],
    extras_require={"dev": ["dagster-webserver"]},
)
