import os

from setuptools import find_packages, setup


def long_description():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, "README.md"), "r") as fh:
        return fh.read()


def get_version():
    version = {}
    with open("dagster_pandas/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster-pandas",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description=(
            "Utilities and examples for working with pandas and dagster, an opinionated "
            "framework for expressing data pipelines"
        ),
        long_description=long_description(),
        long_description_content_type="text/markdown",
        url="https://github.com/dagster-io/dagster",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["dagster_pandas_tests"]),
        include_package_data=True,
        install_requires=["dagster", "pandas<=1.1.4", "matplotlib"],
    )
