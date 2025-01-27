import os
from pathlib import Path

from setuptools import find_packages, setup


def long_description() -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, "README.md"), encoding="utf8") as fh:
        return fh.read()


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_pandas/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-pandas",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description=(
        "Utilities and examples for working with pandas and dagster, an opinionated "
        "framework for expressing data pipelines"
    ),
    long_description=long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/dagster-io/dagster",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_pandas_tests*"]),
    include_package_data=True,
    python_requires=">=3.9,<3.13",
    install_requires=[
        f"dagster{pin}",
        "pandas",
    ],
)
