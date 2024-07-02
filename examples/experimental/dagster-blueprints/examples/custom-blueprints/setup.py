from setuptools import setup, find_packages

setup(
    name="custom-blueprints",
    packages=find_packages(exclude=["custom-blueprints"]),
    install_requires=[
        "dagster",
        "dagster-blueprints",
        "dagster-webserver",
    ],
    extras_require={"dev": ["pytest"]},
)
