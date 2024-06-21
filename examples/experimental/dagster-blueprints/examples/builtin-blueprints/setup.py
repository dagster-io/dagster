from setuptools import find_packages, setup

setup(
    name="builtin-blueprints",
    packages=find_packages(exclude=["builtin-blueprints"]),
    install_requires=[
        "dagster",
        "dagster-blueprints",
        "dagster-webserver",
        "pandas",
    ],
    extras_require={"dev": ["pytest"]},
)
