from setuptools import find_packages, setup

setup(
    name="project_llm_fine_tune",
    packages=find_packages(exclude=["project_llm_fine_tune_tests"]),
    install_requires=[
        "dagster",
        "dagster-openai",
        "dagster-duckdb",
        "pandas",
        "requests",
        "openai",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest", "ruff"]},
)
