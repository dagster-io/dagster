from setuptools import find_packages, setup

setup(
    name="assets_basic_machine_learning",
    packages=find_packages(exclude=["assets_basic_machine_learning_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud",
        "xgboost", 
        "sklearn",
        "numpy",
        "pandas", 
        
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
