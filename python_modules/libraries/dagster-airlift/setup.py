from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_airlift/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
pin = "" if ver == "1!0+dev" or "rc" in ver else f"=={ver}"

# The [in-airflow] subpackage does not have a setup dependency on Airflow because
# Airflow cannot be installed via setup.py reliably. Instead, users need to install
# from a constraints file as recommended by the Airflow project.
# However, to ensure a reliable test and tutorial setup, we pin a version of Airflow
# that is compatible with the current version of dagster-airlift for all supported
# versions of python.
# Eventually, we could consider adding a test suite that runs across different versions of airflow
# to ensure compatibility.
AIRFLOW_REQUIREMENTS = [
    # Requirements for python versions under 3.12.
    "apache-airflow==2.7.3; python_version < '3.12'",
    "marshmallow==3.20.1; python_version < '3.12'",
    "marshmallow==3.23.1; python_version >= '3.12'",
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
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="A toolkit for observing integration and migration between Apache Airflow and Dagster.",
    url=(
        "https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/"
        "dagster-airlift"
    ),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_airlift_tests*", "kitchen-sink", "perf-harness"]),
    requires=CLI_REQUIREMENTS,
    extras_require={
        "core": [
            "dagster==1.10.9",
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
        "test": [
            "pytest",
            "dagster-dbt==0.26.9",
            "dbt-duckdb",
            "boto3",
            "dagster-webserver==1.10.9",
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
