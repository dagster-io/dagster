from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_shared/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster_shared",
    version=get_version(),
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Shared code between dagster and dagster-dg.",
    url=(
        "https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/"
        "dagster-shared"
    ),
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_shared_tests*"]),
    include_package_data=True,
    install_requires=[
        "PyYAML>=5.1",
        "packaging>=20.9",
        "pydantic>=2,<3.0.0",
        "typing_extensions>=4.10.0,<5",
    ],
    extras_require={
        "test": ["pytest"],
    },
    zip_safe=False,
)
