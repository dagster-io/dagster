from setuptools import find_packages, setup

setup(
    name="dagster-helm",
    version="0.0.1",
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Tools for Dagster Helm schema",
    url="https://github.com/dagster-io/dagster/tree/master/helm/dagster/schema",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["schema_tests"]),
    install_requires=["click", "pydantic>=1.10.0,<2.0.0"],
    extras_require={
        "test": [
            # remove pin once minimum supported kubernetes version is 1.19
            "kubernetes<22.6.0",
            "dagster",
            "dagster-aws",
            "dagster-azure",
            "dagster-gcp",
            "dagster-k8s",
        ]
    },
    entry_points={
        "console_scripts": [
            "dagster-helm = schema.cli:main",
        ]
    },
)
