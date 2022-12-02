from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_gcp/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "0+dev" else f"=={ver}"
setup(
    name="dagster-gcp",
    version=ver,
    author="Elementl",
    author_email="hello@elementl.com",
    license="Apache-2.0",
    description="Package for GCP-specific Dagster framework op and resource components.",
    # pylint: disable=line-too-long
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-gcp",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_gcp_tests*"]),
    install_requires=[
        "dagster==1.1.5",
        "dagster_pandas==0.17.5",
        "db-dtypes",  # Required as per https://github.com/googleapis/python-bigquery/issues/1188
        "google-api-python-client",
        "google-cloud-bigquery",
        "google-cloud-storage",
        "oauth2client",
    ],
    # we need `pyarrow` for testing read/write parquet files.
    extras_require={"pyarrow": ["pyarrow"]},
    zip_safe=False,
)
