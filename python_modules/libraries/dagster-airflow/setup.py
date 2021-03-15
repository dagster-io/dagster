from typing import Dict

from setuptools import find_packages, setup  # type: ignore


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster_airflow/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    ver = get_version()
    setup(
        name="dagster-airflow",
        version=ver,
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="Airflow plugin for Dagster",
        url="https://github.com/dagster-io/dagster",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["dagster_airflow_tests"]),
        install_requires=[
            "dagster=={ver}".format(ver=ver),
            "docker",
            "python-dateutil>=2.8.0",
            "lazy_object_proxy",
            "pendulum==1.4.4",
            # https://issues.apache.org/jira/browse/AIRFLOW-6854
            'typing_extensions; python_version>="3.8"',
            # https://github.com/dagster-io/dagster/issues/3858
            "sqlalchemy>=1.0,<1.4.0",
        ],
        extras_require={
            "kubernetes": ["kubernetes>=3.0.0", "cryptography>=2.0.0"],
            "test": [
                # Airflow should be provided by the end user, not us. For example, GCP Cloud
                # Composer ships a fork of Airflow; we don't want to override it with our install.
                # See https://github.com/dagster-io/dagster/issues/2701
                "apache-airflow==1.10.10",
                "boto3==1.9.*",
                "kubernetes==10.0.1",
            ],
        },
        entry_points={"console_scripts": ["dagster-airflow = dagster_airflow.cli:main"]},
    )
