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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["test"]),
    install_requires=[
        "autoflake",
        "boto3",
        "packaging>=20.9",
        "pandas",
        "pytablereader",
        "requests",
        "slackclient>=2,<3",
        "twine==1.15.0",
        "virtualenv==16.5.0",
        "wheel==0.33.6",
        "urllib3",
        # resolve issue with aiohttp pin of chardet for aiohttp<=3.7.3, req'd by slackclient
        # https://github.com/dagster-io/dagster/issues/3539
        "chardet<4.0",
    ],
    entry_points={
        "console_scripts": [
            "dagster-buildkite = automation.buildkite.cli:main",
            "dagster-docs = automation.docs.cli:main",
            "dagster-image = automation.docker.cli:main",
            "dagster-scaffold = automation.scaffold.cli:main",
            "dagster-graphql-client = automation.graphql.python_client.cli:main",
        ]
    },
)
