from setuptools import find_packages, setup

setup(
    name="dagster_conditional_branching",
    version="dev",
    author_email="hello@elementl.com",
    packages=find_packages(exclude=["test"]),
    install_requires=[
        "dagster",
        "pandas",
    ],
    include_package_data=True,
    author="Elementl",
    license="Apache-2.0",
    description="Dagster example for an ETL pipeline that branches based on run-time info",
    url="https://github.com/dagster-io/dagster/tree/master/examples/dagster-conditional-branching",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
