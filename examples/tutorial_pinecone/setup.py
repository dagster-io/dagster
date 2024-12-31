from setuptools import find_packages, setup

setup(
    name="tutorial_pinecone",
    packages=find_packages(exclude=["tutorial_pinecone_tests"]),
    install_requires=[
        "dagster",
        "dagster-duckdb",
        "dagster-duckdb-pandas",
        "pinecone-client",
        "pydantic",
        "pandas",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest", "ruff"]},
)
