import os

from setuptools import find_packages, setup


def long_description():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, "README.rst"), "r", encoding="utf8") as fh:
        return fh.read()


def get_version():
    version = {}
    with open("dagit/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    ver = get_version()
    # dont pin dev installs to avoid pip dep resolver issues
    pin = "" if ver == "0+dev" else f"=={ver}"
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
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["dagit_tests*"]),
        include_package_data=True,
        install_requires=[
            "PyYAML",
            # cli
            "click>=7.0,<9.0",
            f"dagster{pin}",
            f"dagster-graphql{pin}",
            "requests",
            # watchdog
            "watchdog>=0.8.3",
            # notebooks support
            "nbconvert",
            "starlette",
            "uvicorn[standard]",
        ],
        entry_points={
            "console_scripts": ["dagit = dagit.cli:main", "dagit-debug = dagit.debug:main"]
        },
    )
