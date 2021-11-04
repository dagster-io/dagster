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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["schema_tests"]),
    install_requires=["click", "pydantic"],
    extras_require={"test": ["kubernetes"]},
    entry_points={"console_scripts": ["dagster-helm = schema.cli:main",]},
)
