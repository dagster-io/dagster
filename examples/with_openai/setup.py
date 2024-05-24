from setuptools import find_packages, setup

setup(
    name="with_openai",
    packages=find_packages(exclude=["with_openai_tests"]),
    install_requires=[
        "dagster",
        "dagster-aws",
        # Commented to avoid version conflicts with Pyright in the Dagster repo, uncomment when using Dagster+
        # "dagster-cloud",
        "dagster-openai",
        "faiss-cpu==1.8.0",
        "filelock",
        "langchain==0.1.11",
        "langchain-community==0.0.34",
        "langchain-openai==0.1.3",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
