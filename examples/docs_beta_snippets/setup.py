from setuptools import find_packages, setup

setup(
    name="docs_beta_snippets",
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    url="https://github.com/dagster-io/dagster/tree/master/examples/docs_beta_snippets",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["test"]),
    # package not expected to be installed alone, dependencies for use managed in tox.ini
    install_requires=[],
)
