from setuptools import setup

setup(
    name="trigger_pipeline",
    version="dev",
    author_email="hello@elementl.com",
    packages=["trigger_pipeline"],
    include_package_data=True,
    install_requires=["dagster", "dagit", "dagster-graphql", "gql"],
    author="Elementl",
    license="Apache-2.0",
    description="Dagster example for execute pipeline by graphql.",
    url="https://github.com/dagster-io/dagster/tree/master/examples/trigger_pipeline",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
