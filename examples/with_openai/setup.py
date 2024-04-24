from setuptools import find_packages, setup

setup(
    name="with_openai",
    packages=find_packages(exclude=["with_openai_tests"]),
    install_requires=["dagster", "dagster-openai", "langchain==0.1.11"],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
