from setuptools import find_packages, setup

setup(
    name="dagster_examples",
    version="dev",
    author="Elementl",
    author_email="hello@elementl.com",
    license="Apache-2.0",
    description="Dagster Examples",
    url="https://github.com/dagster-io/dagster",
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["test"]),
    # default supports basic tutorial & toy examples
    install_requires=["dagster"],
    extras_require={
        # full is for running the more realistic demos
        "full": [
            "dagstermill",
            "dagster-aws",
            "dagster-cron",
            "dagster-postgres",
            "dagster-pyspark",
            "dagster-slack; python_version >= '3'",
            "dagster-snowflake",
            # These two packages, descartes and geopandas, are used in the airline demo notebooks
            "descartes",
            'geopandas; "win" not in sys_platform',
            "google-api-python-client",
            "google-cloud-storage",
            "keras",
            "lakehouse",
            'matplotlib==3.0.2; python_version >= "3.5"',
            'matplotlib==2.2.4; python_version < "3.5"',
            "mock",
            "moto==1.3.7",
            "pandas>=1.0.0",
            "pytest-mock",
            # Pyspark 2.x is incompatible with Python 3.8+
            'pyspark>=3.0.0; python_version >= "3.8"',
            'pyspark>=2.0.2; python_version < "3.8"',
            "sqlalchemy-redshift>=0.7.2",
            "SQLAlchemy-Utils==0.33.8",
            "tensorflow",
            "dagster-gcp",
        ],
        "dbt": ["dbt-postgres"],
        "airflow": ["dagster_airflow", "docker-compose==1.23.2"],
    },
    include_package_data=True,
)
