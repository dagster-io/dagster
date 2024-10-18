from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup

NON_EDITABLE_INSTALL_DAGSTER_PIN = ">=1.8.10"


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_airlift/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
pin = "" if ver == "1!0+dev" else NON_EDITABLE_INSTALL_DAGSTER_PIN

AIRFLOW_REQUIREMENTS = [
    # Requirements for python versions under 3.12.
    "apache-airflow>=2.0.0; python_version < '3.12'",
    "pendulum>=2.0.0,<3.0.0; python_version < '3.12'",
    # Requirements for python versions 3.12 and above.
    "apache-airflow>=2.9.0; python_version >= '3.12'",
    "pendulum >= 3.0.0; python_version >= '3.12'",
    # Flask-session 0.6 is incompatible with certain airflow-provided test
    # utilities.
    "flask-session<0.6.0",
    # https://github.com/apache/airflow/issues/35234
    "connexion<3.0.0",
]

CLI_REQUIREMENTS = ["click", "structlog"]


setup(
    name="dagster-airlift",
    version="0.0.26",
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Tooling to assist with migrating from Airflow to Dagster.",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
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
    requires=CLI_REQUIREMENTS,
    extras_require={
        "core": [
            f"dagster{pin}",
            *CLI_REQUIREMENTS,
        ],
        # [in-airflow] doesn't directly have a dependency on airflow because Airflow cannot be installed via setup.py reliably. Instead, users need to install from a constraints
        # file as recommended by the Airflow project.
        "in-airflow": CLI_REQUIREMENTS,
        # [tutorial] includes additional dependencies needed to run the tutorial. Namely, the dagster-webserver and the constrained airflow packages.
        "tutorial": [
            "dagster-webserver",
            *AIRFLOW_REQUIREMENTS,
            *CLI_REQUIREMENTS,
        ],
        "mwaa": [
            "boto3>=1.18.0"
        ],  # confirms that mwaa is available in the environment (can't find exactly which version adds mwaa support, but I can confirm that 1.18.0 and greater have it.)
        "dbt": ["dagster-dbt"],
        "k8s": ["dagster-k8s"],
        "test": [
            "pytest",
            "dagster-dbt",
            "dbt-duckdb",
            "boto3",
            "dagster-webserver",
            *AIRFLOW_REQUIREMENTS,
            *CLI_REQUIREMENTS,
        ],
    },
    entry_points={
        "console_scripts": [
            "dagster-airlift = dagster_airlift.cli:cli",
        ]
    },
    zip_safe=False,
)
