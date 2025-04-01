from setuptools import find_packages, setup

setup(
    name="project_prompt_eng",
    packages=find_packages(exclude=["project_prompt_eng_tests"]),
    install_requires=[
        "dagster",
        "dagster-anthropic",
        "pydantic",
        "requests",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest", "ruff==0.8.4"]},
)
