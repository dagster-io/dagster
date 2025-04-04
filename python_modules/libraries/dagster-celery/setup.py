from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> str:
    version: dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_celery/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-celery",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Package for using Celery as Dagster's execution engine.",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-celery",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_celery_tests*"]),
    entry_points={"console_scripts": ["dagster-celery = dagster_celery.cli:main"]},
    python_requires=">=3.9,<3.13",
    install_requires=[
        "dagster==1.10.9",
        "celery>=4.3.0",
        "click>=5.0,<9.0",
        "importlib_metadata<5.0.0; python_version<'3.8'",  # https://github.com/celery/celery/issues/7783
    ],
    extras_require={
        "flower": ["flower"],
        "redis": ["redis"],
        "kubernetes": ["kubernetes"],
        "test": ["docker"],
    },
    zip_safe=False,
)
