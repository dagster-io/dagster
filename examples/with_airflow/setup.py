from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="with_airflow",
        packages=find_packages(exclude=["with_airflow_tests"]),
        install_requires=[
            "dagster",
            "dagit",
            "pytest",
            "dagster_airflow",
            # See https://github.com/dagster-io/dagster/issues/2701
            "apache-airflow==1.10.10",
        ],
    )
