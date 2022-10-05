from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_mlflow/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


setup(
    name="dagster-mlflow",
    version=get_version(),
    author="Elementl",
    author_email="hello@elementl.com",
    license="Apache-2.0",
    description="Package for mlflow Dagster framework components.",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-mlflow",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_mlflow_tests*"]),
    install_requires=[
        "dagster",
        "mlflow<=1.26.0",  # https://github.com/mlflow/mlflow/issues/5968
        "pandas",
    ],
    zip_safe=False,
)
