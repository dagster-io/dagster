from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_managed_elements/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-managed-elements",
    version=ver,
    author="Elementl",
    author_email="hello@elementl.com",
    license="Apache-2.0",
    description="Package for Managed elements with Dagster.",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-managed-elements",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_managed_elements_tests*"]),
    install_requires=["dagster==1.1.13", "requests", "click_spinner"],
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "dagster-managed-elements = dagster_managed_elements.cli:main",
            "dagster-me = dagster_managed_elements.cli:main",
        ]
    },
)
