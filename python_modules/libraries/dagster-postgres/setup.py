from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_postgres/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-postgres",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="A Dagster integration for postgres",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-postgres",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_postgres_tests*"]),
    package_data={
        "dagster-postgres": [
            "dagster_postgres/alembic/*",
        ]
    },
    include_package_data=True,
    python_requires=">=3.9,<3.13",
    install_requires=[f"dagster{pin}", "psycopg2-binary"],
    zip_safe=False,
)
