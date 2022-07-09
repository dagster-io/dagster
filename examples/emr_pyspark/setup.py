from setuptools import find_packages, setup

setup(
    name="emr_pyspark",
    version="0+dev",
    author_email="hello@elementl.com",
    packages=find_packages(exclude=["emr_pyspark_tests*"]),
    include_package_data=True,
    install_requires=["dagster", "dagit", "dagster-aws", "dagster-pyspark"],
    author="Elementl",
    license="Apache-2.0",
    description="Example of using Dagster with PySpark on Amazon EMR",
    url="https://github.com/dagster-io/dagster/tree/master/examples/emr_pyspark",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
