from typing import Dict

from setuptools import find_packages, setup  # type: ignore


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("airflow_op_to_dagster_op/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    ver = get_version()
    # dont pin dev installs to avoid pip dep resolver issues
    pin = "" if ver == "dev" else f"=={ver}"
    setup(
        name="airflow-op-to-dagster-op",
        version=ver,
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="Utility to convert Airflow operator to Dagster op",
        url="https://github.com/dagster-io/dagster",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["airflow_op_to_dagster_op_tests"]),
        install_requires=[
            f"dagster{pin}",
            'typing_extensions; python_version>="3.8"',
            'apache-airflow==2.2.0',
            # apache-airflow-providers-docker required for DockerOperator
            "apache-airflow-providers-docker==2.2.0",
            "apache-airflow-providers-sqlite==2.0.1",
            "apache-airflow-providers-apache-hive==2.0.2",
            # required by HiveCliHook
            "pandas",
        ],
        extras_require={
            "test": [],
        },
    )
