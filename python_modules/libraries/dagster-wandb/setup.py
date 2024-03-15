from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagster_wandb/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-wandb",
    version=get_version(),
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Package for wandb Dagster components.",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-wandb",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_wandb_tests*"]),
    python_requires=">=3.8,<3.13",
    install_requires=[
        "dagster==1.6.11",
        "wandb>=0.15.11,<1.0",
    ],
    extras_require={"dev": ["cloudpickle", "joblib", "callee", "dill"]},
    zip_safe=False,
)
