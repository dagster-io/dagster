from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_airlift/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-airlift",
    version=get_version(),
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Tooling to assist with migrating from Airflow to Dagster.",
    url=(
        "https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/"
        "dagster-airlift"
    ),
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_airlift_tests*", "examples*"]),
    install_requires=[
        f"dagster{pin}",
        f"dagster-dbt{pin}",
        "apache-airflow>=2.0.0,<2.8",
        # Flask-session 0.6 is incompatible with certain airflow-provided test
        # utilities.
        "flask-session<0.6.0",
        "connexion<3.0.0",  # https://github.com/apache/airflow/issues/35234
        "dbt-duckdb",
        "pendulum>=2.0.0,<3.0.0",
    ],
    extras_require={
        "mwaa": ["boto3"],
    },
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "dagster-airlift = dagster_airlift.cli:main",
        ]
    },
)
