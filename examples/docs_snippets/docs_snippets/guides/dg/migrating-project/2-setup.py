from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="my_existing_project",
    version="0.1.0",
    description="Add your description here",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.9,<3.13",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-components",
    ],
    extras_require={
        "dev": [
            "dagster-webserver",
            "pytest>8",
        ]
    },
)
