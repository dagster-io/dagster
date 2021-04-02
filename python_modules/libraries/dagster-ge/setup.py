from typing import Dict

from setuptools import find_packages, setup  # type: ignore


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster_ge/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster-ge",
        version=get_version(),
        author="Elementl",
        license="Apache-2.0",
        description="Package for GE-specific Dagster framework solid and resource components.",
        # pylint: disable=line-too-long
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-ge",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        install_requires=[
            "dagster",
            "dagster-pandas",
            "pandas",
            "great_expectations >=0.11.9, !=0.12.8, <0.13.7",  # 0.13.7 incompatible with sqlalchemy >= 1.4.0
        ],
        zip_safe=False,
    )
