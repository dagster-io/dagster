from setuptools import find_packages, setup

setup(
    name="project_ask_ai_dagster",
    packages=find_packages(exclude=["project_ask_ai_dagster_tests"]),
    install_requires=[
        "dagster",
        "dagster-openai",
        "dagster-duckdb",
        "pandas",
        "openai",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest", "ruff"]},
)
