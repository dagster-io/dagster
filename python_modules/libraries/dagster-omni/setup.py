from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_omni/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster_omni",
    version=get_version(),
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Package for integrating Omni with Dagster.",
    url=("https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-omni"),
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_omni_tests*"]),
    include_package_data=True,
    install_requires=[
        "dagster==1.12.7",
        "aiohttp",
        "python-dateutil",
    ],
    zip_safe=False,
)
