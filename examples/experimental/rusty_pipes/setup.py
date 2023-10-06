from setuptools import find_packages, setup

setup(
    name="rusty_pipes",
    packages=find_packages(exclude=["rusty_pipes"]),
    install_requires=[
        "dagster",
        "polars",
        "dagster-pipes",
    ],
    license="Apache-2.0",
    description="Example showing how Dagster Pipes can be used with Rust.",
    url="https://github.com/dagster-io/dagster/tree/master/examples/experimental/rusty_pipes",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    extras_require={
        "dev": [
            "pytest",
        ]
    },
)
