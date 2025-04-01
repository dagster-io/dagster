from pathlib import Path

from setuptools import find_packages, setup


def get_version() -> tuple[str, str]:
    version: dict[str, str] = {}
    kubernetes_version: dict[str, str] = {}

    with open(Path(__file__).parent / "dagster_k8s/version.py", encoding="utf8") as fp:
        exec(fp.read(), version)

    with open(Path(__file__).parent / "dagster_k8s/kubernetes_version.py", encoding="utf8") as fp:
        exec(fp.read(), kubernetes_version)

    return version["__version__"], kubernetes_version["KUBERNETES_VERSION_UPPER_BOUND"]


(
    ver,
    KUBERNETES_VERSION_UPPER_BOUND,
) = get_version()
# dont pin dev installs to avoid pip dep resolver issues
pin = "" if ver == "1!0+dev" else f"=={ver}"
setup(
    name="dagster-k8s",
    version=ver,
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="A Dagster integration for k8s",
    url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-k8s",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(exclude=["dagster_k8s_tests*"]),
    include_package_data=True,
    python_requires=">=3.9,<3.13",
    install_requires=[
        f"dagster{pin}",
        f"kubernetes<{KUBERNETES_VERSION_UPPER_BOUND}",
        # exclude a google-auth release that added an overly restrictive urllib3 pin that confuses dependency resolvers
        "google-auth!=2.23.1",
    ],
    zip_safe=False,
)
