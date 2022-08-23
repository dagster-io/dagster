from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="with_pyspark_emr",
        packages=find_packages(exclude=["with_pyspark_emr_tests"]),
        install_requires=[
            "dagster",
            "dagster-aws",
            "dagster-pyspark",
        ],
        extras_require={"dev": ["dagit", "pytest"]},
    )
