from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_gcp/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-gcp",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Package for GCP-specific Dagster framework op and resource components.",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-gcp",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_gcp_tests*"]),
    include_package_data=True,
    python_requires=">=3.10,<3.15",
    install_requires=[
        "dagster==1.12.7",
        "dagster_pandas==0.28.7",
        "db-dtypes",  # Required as per https://github.com/googleapis/python-bigquery/issues/1188
        "google-api-python-client",
        "google-cloud-bigquery>=1.28.3",  # earliest version that imports without protobuf errors
        "google-cloud-storage",
        "oauth2client",
    ],
    # we need `pyarrow` for testing read/write parquet files.
    extras_require={
        "pyarrow": ["pyarrow"],
        "test": ["gcp-storage-emulator"],
        "dataproc": ["google-cloud-dataproc"],
    },
    zip_safe=False,
)
