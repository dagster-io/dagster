import os
from pathlib import Path

from setuptools import find_packages, setup


def long_description():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, "README.rst"), "r", encoding="utf8") as fh:
        return fh.read()


def get_version():
    version = {}
    with open(Path(__file__).parent / "dagit/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagit",
    version=ver,
    author="Elementl",
    author_email="hello@elementl.com",
    license="Apache-2.0",
    description="Web UI for dagster.",
    long_description=long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/dagster-io/dagster",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagit_tests*"]),
    include_package_data=True,
    install_requires=[
        # cli
        "click>=7.0,<9.0",
        "dagster==1.1.13",
        "dagster-graphql==1.1.13",
        "starlette",
        "uvicorn[standard]",
    ],
    extras_require={
        "notebook": ["nbconvert"],  # notebooks support
        "test": ["starlette[full]"],  # TestClient deps in full
    },
    entry_points={"console_scripts": ["dagit = dagit.cli:main", "dagit-debug = dagit.debug:main"]},
)
