from setuptools import find_packages, setup

setup(
    name="dbt-job-blueprints",
    packages=find_packages(exclude=["dbt-job-blueprints"]),
    install_requires=[
        "dagster",
        "dagster-blueprints",
        "dagster-webserver",
    ],
    extras_require={"dev": ["pytest"]},
)
