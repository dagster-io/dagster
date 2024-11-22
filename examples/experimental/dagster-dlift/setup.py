from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup

NON_EDITABLE_INSTALL_DAGSTER_PIN = ">=1.8.10"


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_dlift/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)
    return version["__version__"]


ver = get_version()
pin = "" if ver == "1!0+dev" else NON_EDITABLE_INSTALL_DAGSTER_PIN
setup(
    name="dagster-dlift",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="An integration allowing Dagster to observe and execute dbt cloud.",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    url=("https://github.com/dagster-io/dagster/tree/master/examples/experimental/dagster-dlift"),
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    requires=[f"dagster{pin}"],
    packages=find_packages(exclude=["dagster_dlift_tests*", "examples*"]),
    zip_safe=False,
)
