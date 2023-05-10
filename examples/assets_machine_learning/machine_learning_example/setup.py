from setuptools import find_packages, setup

setup(
    name="machine_learning_example",
    packages=find_packages(exclude=["machine_learning_example_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud", 
        "pandas", 
        "numpy", 
        "xgboost", 
        "scikit-learn",
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
