from setuptools import find_packages, setup

setup(
    name="project_fully_featured",
    version="1!0+dev",
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["test"]),
    package_data={"project_fully_featured": ["hacker_news_dbt/*"]},
    install_requires=[
        "aiobotocore",
        "dagster",
        "dagster-aws",
        "dagster-dbt",
        "dagster-pandas",
        "dagster-pyspark",
        "dagster-slack",
        "dagster-postgres",
        "dbt-duckdb",
        "dbt-snowflake",
        "duckdb!=0.3.3, <= 6.0.0",  # missing wheels
        "mock",
        "pandas",
        "pyarrow>=4.0.0",
        "pyspark",
        "requests",
        "gcsfs",
        "fsspec",
        "s3fs",
        "scipy",
        "scikit-learn",
        "sqlalchemy!=1.4.42",  # workaround for https://github.com/snowflakedb/snowflake-sqlalchemy/issues/350
        "snowflake-sqlalchemy",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"], "tests": ["mypy", "pylint", "pytest"]},
)
