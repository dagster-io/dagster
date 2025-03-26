from setuptools import find_packages, setup

setup(
    name="docs_snippets",
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    url="https://github.com/dagster-io/dagster/tree/master/examples/docs_snippets",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["test"]),
    install_requires=[],
    extras_require={
        "full": [
            "click",
            "matplotlib",
            # matplotlib-inline 0.1.5 is causing mysterious
            # "'NoneType' object has no attribute 'canvas'" errors in the tests that involve
            # Jupyter notebooks
            "matplotlib-inline<=0.1.3",
            "moto[s3]<5.0",
            "numpy",
            "pandas",
            "pandera",
            "plotly",
            "pytest",
            "requests",
            "seaborn",
            "scikit-learn",
            "slack_sdk",
            "syrupy",
            "dbt-duckdb",
            "xgboost",
            "dagster-webserver[test]",
            "flaky",
        ],
    },
)
