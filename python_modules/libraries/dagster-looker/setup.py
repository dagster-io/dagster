from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_looker/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster_looker",
    version=get_version(),
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="",
    url=(
        "https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/"
        "dagster-looker"
    ),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_looker_tests*"]),
    install_requires=[
        "dagster==1.10.9",
        "lkml",
        # Remove pin after resolution of: https://github.com/looker-open-source/sdk-codegen/issues/1518
        "looker_sdk<24.18.0",
        # Dialect.SET_OP_DISTINCT_BY_DEFAULT was introduced in version 25.19.0:
        # https://github.com/tobymao/sqlglot/blob/v25.19.0/sqlglot/dialects/dialect.py
        "sqlglot>=25.19.0",
        "python-liquid<2",
        "cattrs<23.2",  # https://github.com/looker-open-source/sdk-codegen/issues/1410
    ],
    zip_safe=False,
)
