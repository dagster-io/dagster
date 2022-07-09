from setuptools import setup  # type: ignore

setup(
    name="software_defined_assets",
    version="0+dev",
    author_email="hello@elementl.com",
    packages=["software_defined_assets"],  # same as name
    install_requires=["dagster"],  # external packages as dependencies
    author="Elementl",
    license="Apache-2.0",
    description="Dagster example of software-defined assets.",
    url="https://github.com/dagster-io/dagster/tree/master/examples/software_defined_assets",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    extras_require={"test": ["pandas", "pyarrow; python_version < '3.9'", "pyspark"]},
    python_requires=">=3.6,<=3.10",
)
