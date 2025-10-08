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
        "langchain<0.4",
        "langchain-community<0.4",
        "langchain-openai<0.4",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
