from setuptools import find_packages, setup

setup(
    name="automation",
    version="0.0.1",
    author="Elementl",
    author_email="hello@elementl.com",
    license="Apache-2.0",
    description="Tools for infrastructure automation",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/automation",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["automation_tests*"]),
    install_requires=[
        "autoflake",
        "boto3",
        # packaging v22 has build compatibility issues with dbt as of 2022-12-07
        # upper bound can be removed as soon as BK passes with packaging >=22
        "packaging>=20.9,<22",
        "pandas",
        "pytablereader",
        "requests",
        "twine==1.15.0",
        "virtualenv==20.13.2",
        "wheel==0.33.6",
        "urllib3",
    ],
    extras_require={
        "buildkite": [
            "dagster",  # Support buildkite conditional running of tests
        ]
    },
    entry_points={
        "console_scripts": [
            "dagster-image = automation.docker.cli:main",
            "dagster-graphql-client = automation.graphql.python_client.cli:main",
        ]
    },
)
