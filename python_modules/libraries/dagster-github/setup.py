from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open("dagster_github/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    ver = get_version()
    # dont pin dev installs to avoid pip dep resolver issues
    pin = "" if ver == "0+dev" else f"=={ver}"
    setup(
        name="dagster-github",
        version=ver,
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="A Github client resource for interacting with the github API with a github App",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-github",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["dagster_github_tests*"]),
        install_requires=[
            f"dagster{pin}",
            # Using a Github app requires signing your own JWT :(
            # https://developer.github.com/apps/building-github-apps/authenticating-with-github-apps/
            "pyjwt[crypto]",
            # No officially supported python sdk for github :(
            "requests",
        ],
        zip_safe=False,
    )
