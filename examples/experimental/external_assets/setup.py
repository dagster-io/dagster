from setuptools import find_packages, setup

setup(
    name="external_assets",
    packages=find_packages(),
    install_requires=["dagster>=1.5.1", "dagster-k8s>=0.21.1"],
    extras_require={"dev": ["dagit", "pytest"]},
)
