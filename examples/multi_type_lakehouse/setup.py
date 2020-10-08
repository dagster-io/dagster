from setuptools import setup

setup(
    name="multi_type_lakehouse",
    version="dev",
    description="Dagster example for using Lakehouse API with Pandas and Pyspark",
    author="Elementl",
    author_email="hello@elementl.com",
    packages=["multi_type_lakehouse"],  # same as name
    license="Apache-2.0",
    url="https://github.com/dagster-io/dagster/tree/master/examples/multi_type_lakehouse",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
