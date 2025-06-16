from setuptools import find_packages, setup

setup(
    name="project_ask_ai_dagster",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "langchain",
        "langchain-core",
        "gql",
        "python-dotenv",
        "langchain-community",
        "langchain-openai",
        "langchain-chroma",
        "dagster",
        "dagster-dg-cli",
        "dagster-openai",
        "dagster_duckdb",
        "chromadb",
        "tokenizers",
        "tenacity",
        "tqdm",
        "bs4",
        "lxml",
        "openai",
        "pinecone",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest", "ruff"]},
)
