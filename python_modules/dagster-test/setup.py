from setuptools import find_packages, setup

setup(
    name="dagster-test",
    version="1!0+dev",
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="A Dagster integration for test",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-test",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_test_tests*"]),
    python_requires=">=3.8,<3.13",
    install_requires=[
        "dagster",
        "pyspark",
        "rich",
    ],
    zip_safe=False,
)
