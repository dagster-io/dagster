from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="with_pyspark_emr",
        packages=find_packages(exclude=["with_pyspark_emr_tests"]),
        install_requires=[
            "dagster",
            "dagit",
            "pytest",
            "dagster-aws",
            "dagster-pyspark",
        ],
    )
