from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(Path(__file__).parent / "dagstermill/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagstermill",
    version=ver,
    description="run notebooks using the Dagster tools",
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    packages=find_packages(exclude=["dagstermill_tests*"]),
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "dagster==1.5.2",
        # ipykernel 5.4.0 and 5.4.1 broke papermill
        # see https://github.com/dagster-io/dagster/issues/3401,
        # https://github.com/nteract/papermill/issues/519,
        # https://github.com/ipython/ipykernel/issues/568
        "ipykernel>=4.9.0,!=5.4.0,!=5.4.1",
        # See: https://github.com/mu-editor/mu/pull/1844
        # ipykernel<6 depends on ipython_genutils, but it isn't explicitly
        # declared as a dependency. It also depends on traitlets, which
        # incidentally brought ipython_genutils, but in v5.1 it was dropped, so as
        # a workaround we need to manually specify it here
        "ipython_genutils>=0.2.0",
        "packaging>=20.9",
        "papermill>=1.0.0",
        "scrapbook>=0.5.0",
        "nbconvert",
        "jupyter-client<8",  # jupyter-client 8 causing test hangs
    ],
    extras_require={
        "test": [
            "matplotlib",
            "scikit-learn>=0.19.0",
            "tqdm<=4.48",  # https://github.com/tqdm/tqdm/issues/1049
        ]
    },
    entry_points={"console_scripts": ["dagstermill = dagstermill.cli:main"]},
)
