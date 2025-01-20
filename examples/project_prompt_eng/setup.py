from setuptools import find_packages, setup

setup(
    name="project_prompt_eng",
    packages=find_packages(exclude=["project_prompt_eng_tests"]),
    install_requires=[
        "dagster",
        "dagster-openai",
        "openai",
        "pydantic",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest", "ruff"]},
)