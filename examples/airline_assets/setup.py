from setuptools import setup  # type: ignore

setup(
    name="airline_assets",
    version="0+dev",
    author_email="hello@elementl.com",
    packages=["airline_assets"],  # same as name
    install_requires=["dagster", "pandas"],  # external packages as dependencies
    author="Elementl",
    license="Apache-2.0",
    description="Dagster example of op and graph-backed assets.",
    url="https://github.com/dagster-io/dagster/tree/master/examples/airline_assets",
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
