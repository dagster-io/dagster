from setuptools import find_packages, setup

pin = ""
setup(
    name="dagster_sigma",
    version="0.0.10",
    author="Dagster Labs",
    author_email="hello@dagsterlabs.com",
    license="Apache-2.0",
    description="Build assets representing Sigma dashboards.",
    url=(
        "https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/"
        "dagster-sigma"
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
    packages=find_packages(exclude=["dagster_sigma_tests*"]),
    install_requires=[
        f"dagster{pin}",
        "sqlglot",
    ],
    include_package_data=True,
    python_requires=">=3.8,<3.13",
    zip_safe=False,
)
