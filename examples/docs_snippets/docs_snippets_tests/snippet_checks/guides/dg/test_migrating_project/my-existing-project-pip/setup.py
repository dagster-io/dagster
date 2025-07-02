from setuptools import find_packages, setup

setup(
    name="my_existing_project",
    version="0.1.0",
    description="Add your description here",
    python_requires=">=3.9,<=3.13.3",
    packages=find_packages(),
    install_requires=[
        "dagster",
    ],
    extras_require={
        "dev": [
            "dagster-webserver",
            "pytest>8",
        ]
    },
)
