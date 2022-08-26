from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster_pandera/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=exec-used

    return version["__version__"]


if __name__ == "__main__":
    ver = get_version()
    # dont pin dev installs to avoid pip dep resolver issues
    pin = "" if ver == "0+dev" else f"=={ver}"
    setup(
        name="dagster-pandera",
        version=ver,
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description=("Integration layer for dagster and pandera."),
        url="https://github.com/dagster-io/dagster",
        classifiers=[
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["dagster_pandera_tests*"]),
        include_package_data=True,
        install_requires=[f"dagster{pin}", "pandas", "pandera>=0.9.0"],
        extras_require={
            "test": [
                "pytest",
            ],
        },
    )
