from setuptools import find_packages, setup

setup(
    name="basic_pyspark",
    version="0+dev",
    author_email="hello@elementl.com",
    packages=find_packages(exclude=["basic_pyspark_tests*"]),
    include_package_data=True,
    install_requires=["dagster", "dagit", "pyspark"],
    python_requires=">=3.6,<=3.10",
    author="Elementl",
    license="Apache-2.0",
    description="A basic Dagster with PySpark example.",
    url="https://github.com/dagster-io/dagster/tree/master/examples/basic_pyspark",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
