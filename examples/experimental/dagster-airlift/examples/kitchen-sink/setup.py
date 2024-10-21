from pathlib import Path
from typing import Dict

from setuptools import find_packages, setup


def get_version() -> str:
    version: Dict[str, str] = {}
    with open(
        Path(__file__).parent / ".." / ".." / "dagster_airlift/version.py", encoding="utf8"
    ) as fp:
        exec(fp.read(), version)

    return version["__version__"]


ver = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"

setup(
    name="kitchen-sink",
    packages=find_packages(),
    install_requires=[
        f"dagster{pin}",
        f"dagster-webserver{pin}",
        f"dagster-airlift[core,in-airflow]{pin}",
    ],
    extras_require={"test": ["pytest"]},
)
