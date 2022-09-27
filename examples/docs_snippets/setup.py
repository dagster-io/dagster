from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="docs_snippets",
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        url="https://github.com/dagster-io/dagster/tree/master/examples/docs_snippets",
        classifiers=[
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        install_requires=[
            "dagit",
            "dagster",
            "dagstermill",
            "dagster-airflow",
            "dagster-aws",
            "dagster-celery",
            "dagster-dbt",
            "dagster-dask",
            "dagster-gcp",
            "dagster-graphql",
            "dagster-k8s",
            "dagster-postgres",
            "dagster-slack",
        ],
        extras_require={
            "full": [
                "click",
                "matplotlib",
                # matplotlib-inline 0.1.5 is causing mysterious
                # "'NoneType' object has no attribute 'canvas'" errors in the tests that involve
                # Jupyter notebooks
                "matplotlib-inline<=0.1.3",
                "moto==1.3.16",
                "numpy",
                "pandas",
                "pandera",
                "pytest",
                "requests",
                "seaborn",
                "scikit-learn",
                "slack_sdk",
                "snapshottest",
                "dagit[test]",
            ]
        },
    )
