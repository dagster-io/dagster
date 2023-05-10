from setuptools import find_packages, setup

setup(
    name="ml_example",
    packages=find_packages(exclude=["ml_example_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud", 
        "xgboost",
        "pandas",
        "numpy",
        "scikit-learn",
        "mlflow",
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
