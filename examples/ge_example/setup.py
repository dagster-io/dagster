from setuptools import setup

setup(
    name="ge_example",
    version="dev",
    author_email="hello@elementl.com",
    packages=["ge_example"],
    include_package_data=True,
    install_requires=[
        "dagster",
        "dagit",
        "dagster-ge",
        "great_expectations",
    ],
    author="Elementl",
    license="Apache-2.0",
    description="Dagster example for using the Great Expectations integration.",
    url="https://github.com/dagster-io/dagster/tree/master/examples/simple_lakehouse",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
