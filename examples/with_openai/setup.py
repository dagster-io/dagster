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
        "langchain==0.3.7",
        "langchain-community==0.3.5",
        "langchain-openai==0.2.5",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
