from setuptools import find_packages, setup


def get_version() -> str:
    return "1!0+dev"
    # Uncomment when ready to publish
    # version: Dict[str, str] = {}
    # with open(Path(__file__).parent / "dagster_powerbi/version.py", encoding="utf8") as fp:
    #     exec(fp.read(), version)

    # return version["__version__"]


# TODO - add your package to scripts/install_dev_python_modules.py

ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster_powerbi",
    version=get_version(),
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="",  # TODO - fill out description
    url=(
        "https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/"
        "dagster-powerbi"
    ),
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_powerbi_tests*"]),
    install_requires=[
        f"dagster{pin}",
        # TODO - fill in remaining dependencies
    ],
    zip_safe=False,
)
