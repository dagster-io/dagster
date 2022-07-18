from setuptools import setup  # type: ignore

setup(
    name="local_to_production",
    version="0+dev",
    author_email="hello@elementl.com",
    packages=["local_to_production"],  # same as name
    install_requires=[
        "dagster",
        "dagster-snowflake",
        "dagster-snowflake-pandas",
        "dagit",
        "pandas",
    ],  # external packages as dependencies
    author="Elementl",
    license="Apache-2.0",
    description="Dagster example of local development and production deployment.",
    url="https://github.com/dagster-io/dagster/tree/master/examples/local_to_production",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
