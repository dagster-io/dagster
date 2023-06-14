from setuptools import find_packages, setup

setup(
    name="assets_mlflow_machine_learning",
    packages=find_packages(exclude=["assets_mlflow_machine_learning_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud"
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
