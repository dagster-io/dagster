from setuptools import find_packages, setup

setup(
    name="with_openai",
    packages=find_packages(exclude=["with_openai_tests"]),
    install_requires=[
        "dagster",
        "dagster-aws",
        "dagster-openai",
        "faiss-cpu==1.8.0",
        "filelock",
        "langchain==0.2.7",
        "langchain-community==0.2.9",
        "langchain-openai==0.1.14",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
