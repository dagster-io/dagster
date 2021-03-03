from typing import Dict

from setuptools import find_packages, setup  # type: ignore


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster_gcp/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster-gcp",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="Package for GCP-specific Dagster framework solid and resource components.",
        # pylint: disable=line-too-long
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-gcp",
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
            "dagster_pandas",
            "google-api-python-client<2.0.0",
            "google-cloud-bigquery>=1.19.*",
            "google-cloud-storage",
            "oauth2client",
        ],
        extras_require={"pyarrow": ["pyarrow; python_version < '3.9'"]},
        zip_safe=False,
    )
