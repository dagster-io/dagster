from typing import Dict

from setuptools import find_packages, setup  # type: ignore


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("lakehouse/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    ver = get_version()
    # dont pin dev installs to avoid pip dep resolver issues
    pin = "" if ver == "dev" else f"=={ver}"
    setup(
        name="lakehouse",
        version=ver,
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/lakehouse",
        install_requires=[f"dagster{pin}"],
        packages=find_packages(exclude=["test"]),
        entry_points={"console_scripts": ["house = lakehouse.cli:main"]},
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        zip_safe=False,
    )
