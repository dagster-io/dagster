from setuptools import find_packages, setup

setup(
    name="dagster-helm",
    version="0.0.1",
    author="Elementl",
    author_email="hello@elementl.com",
    license="Apache-2.0",
    description="Tools for Dagster Helm schema",
    url="https://github.com/dagster-io/dagster/tree/master/helm/dagster/schema",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["schema_tests"]),
    install_requires=["click", "pydantic"],
    extras_require={
        "test": [
            "dagster[test]",
            # remove pin once minimum supported kubernetes version is 1.19
            "kubernetes<22.6.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "dagster-helm = schema.cli:main",
        ]
    },
)
