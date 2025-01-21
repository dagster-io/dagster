from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_pipes/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
desc = "Toolkit for Dagster integrations with transform logic outside of Dagster"
setup(
    name="dagster-pipes",
    version=get_version(),
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description=desc,
    long_description=desc,
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/dagster-pipes",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_pipes_tests*"]),
    include_package_data=True,
    python_requires=">=3.9,<3.13",
    zip_safe=False,
    extras_require={
        "stubs": [
            "google-cloud-storage",
        ]
    },
)
