from pathlib import Path

from setuptools import find_packages, setup


def get_version():
    version = {}
    with open(Path(__file__).parent / "dagster_mariadb/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-mariadb",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="A Dagster integration for MariaDB",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-mariadb",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_mariadb_tests*"]),
    include_package_data=True,
    python_requires=">=3.9,<3.14",
    install_requires=[
        f"dagster{pin}",
        "sqlalchemy>=1.4.0",
        "pymysql>=1.0.0",
        "pandas>=1.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov",
            "black",
            "isort",
            "mypy",
        ],
    },
    zip_safe=False,
)

