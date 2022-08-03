from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="with_pyspark",
        packages=find_packages(exclude=["with_pyspark_tests"]),
        install_requires=[
            "dagster",
            "dagit",
            "pytest",
            "dagster-spark",
            "dagster-pyspark",
        ],
    )
