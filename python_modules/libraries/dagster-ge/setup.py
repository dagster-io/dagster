from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster_ge/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    ver = get_version()
    # dont pin dev installs to avoid pip dep resolver issues
    pin = "" if ver == "0+dev" else f"=={ver}"
    setup(
        name="dagster-ge",
        version=ver,
        author="Elementl",
        license="Apache-2.0",
        description="Package for GE-specific Dagster framework op and resource components.",
        # pylint: disable=line-too-long
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-ge",
        classifiers=[
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["dagster_ge_tests*"]),
        install_requires=[
            "dagster==1.0.13",
            "dagster-pandas==0.16.13",
            "pandas",
            "great_expectations >=0.11.9, !=0.12.8, !=0.13.17, !=0.13.27",
        ],
        zip_safe=False,
    )
