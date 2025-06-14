from setuptools import find_packages, setup

setup(
    name="project_prompt_eng",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "dagster",
        "dagster-dg-cli",
        "dagster-anthropic",
        "pydantic",
        "requests",
    ],
    extras_require={
        "dev": [
            "ruff",
            "pytest",
            "dagster-webserver",
        ]
    },
)
