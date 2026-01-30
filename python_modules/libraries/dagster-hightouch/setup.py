from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_hightouch/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)
    return version["__version__"]


ver = get_version()

pin = "" if ver == "1!0+dev" else f"=={ver}"

setup(
    name="dagster-hightouch",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Package for integrating Hightouch with Dagster.",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-hightouch",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_hightouch_tests*"]),
    include_package_data=True,
    python_requires=">=3.10,<3.14",
    install_requires=[
        "dagster==1.12.13",
        "requests",
        "python-dateutil",
    ],
    entry_points={
        "dagster_dg_cli.registry_modules": [
            "dagster_hightouch = dagster_hightouch",
        ],
    },
    zip_safe=False,
)
