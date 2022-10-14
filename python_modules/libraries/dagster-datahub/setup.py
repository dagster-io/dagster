from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster_datahub/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    ver = get_version()
    # dont pin dev installs to avoid pip dep resolver issues
    pin = "" if ver == "0+dev" else f"=={ver}"
    setup(
        name="dagster-datahub",
        version=ver,
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="Package for Datahub-specific Dagster framework solid and resource components.",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-datahub",
        classifiers=[
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["dagster_datahub_tests*"]),
        include_package_data=True,
        install_requires=[
            "acryl-datahub[datahub-rest, datahub-kafka]<0.8.41.2",
            "dagster==1.0.13",
            "packaging",
            "requests",
        ],
        extras_require={},
        zip_safe=False,
    )
