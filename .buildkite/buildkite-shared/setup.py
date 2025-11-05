from setuptools import find_packages, setup

setup(
    name="buildkite-shared",
    version="0.0.1",
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Shared tools for buildkite automation",
    url="https://github.com/dagster-io/dagster/tree/master/.buildkite/buildkite-shared",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["test"]),
    install_requires=[
        "typing_extensions>=4.2",
    ],
)
