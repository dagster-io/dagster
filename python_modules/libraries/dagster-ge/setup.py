from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_ge/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-ge",
    version=ver,
    author="Dagster Labs",
    license="Apache-2.0",
    description="Package for GE-specific Dagster framework op and resource components.",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-ge",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_ge_tests*"]),
    python_requires=">=3.8,<3.13",
    install_requires=[
        "dagster==1.6.13",
        "dagster-pandas==0.22.13",
        "pandas",
        "great_expectations >=0.11.9, !=0.12.8, !=0.13.17, !=0.13.27, <0.17.12",
    ],
    zip_safe=False,
)
