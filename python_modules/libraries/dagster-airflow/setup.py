from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_airflow/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-airflow",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Airflow plugin for Dagster",
    url="https://github.com/dagster-io/dagster",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_airflow_tests*"]),
    install_requires=[
        "dagster==1.5.2",
        "docker>=5.0.3,<6.0.0",
        "lazy_object_proxy",
        "pendulum",
    ],
    project_urls={
        # airflow will embed a link this in the providers page UI
        "project-url/documentation": "https://docs.dagster.io",
    },
    extras_require={
        "kubernetes": ["kubernetes>=3.0.0", "cryptography>=2.0.0"],
        "test_airflow_2": [
            "apache-airflow>=2.0.0",
            "boto3>=1.26.7",
            "kubernetes>=10.0.1",
            "apache-airflow-providers-docker>=3.2.0,<4",
            "apache-airflow-providers-apache-spark",
            # Logging messages are set to debug starting 4.1.1
            "apache-airflow-providers-http<4.1.1",
        ],
        "test_airflow_1": [
            "apache-airflow>=1.0.0,<2.0.0",
            "boto3>=1.26.7",
            "kubernetes>=10.0.1",
            # pinned based on certain incompatible versions of Jinja2, which is itself pinned
            # by apache-airflow==1.10.10
            "markupsafe<=2.0.1",
            # New WTForms release breaks the version of airflow used by tests
            "WTForms<3.0.0",
            # https://github.com/dagster-io/dagster/issues/3858
            "sqlalchemy>=1.0,<1.4.0",
            "marshmallow-sqlalchemy<0.26.0",
        ],
    },
    entry_points={
        # airflow 1.0/2.0 plugin format
        "airflow.plugins": ["dagster_airflow = dagster_airflow.__init__:DagsterAirflowPlugin"],
        # airflow 2.0 provider format
        "apache_airflow_provider": ["provider_info=dagster_airflow.__init__:get_provider_info"],
    },
)
