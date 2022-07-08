from setuptools import setup

setup(
    name="memoized_development",
    version="0+dev",
    author_email="hello@elementl.com",
    packages=["memoized_development"],  # same as name
    install_requires=["dagster"],  # external packages as dependencies
    author="Elementl",
    license="Apache-2.0",
    description="Example for using versioning and memoization with Dagster..",
    url="https://github.com/dagster-io/dagster/tree/master/examples/memoized_development",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
