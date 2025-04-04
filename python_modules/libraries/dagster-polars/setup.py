from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_polars/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-polars",
    version=get_version(),
    author="Daniel Gafni",
    author_email="danielgafni16@gmail.com",
    license="Apache-2.0",
    description="Dagster integration library for Polars",
    url=(
        "https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-polars"
    ),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_polars_tests*"]),
    include_package_data=True,
    python_requires=">=3.9,<3.13",
    install_requires=[
        "dagster==1.10.9",
        "polars>=0.20.0",
        "pyarrow>=8.0.0",
        "typing-extensions>=4.7.0",
        "universal_pathlib>=0.1.4",
    ],
    extras_require={
        "deltalake": ["deltalake>=0.25.0"],
        "gcp": ["dagster-gcp>=0.19.5"],
        "test": [
            "polars>=1.24.0",
            "pytest>=8",
            "hypothesis[zoneinfo]>=6.89.0",
            "deepdiff>=6.3.0",
            "pytest-cases>=3.6.14",
            "pytest_mock",
        ],
    },
    zip_safe=False,
)
