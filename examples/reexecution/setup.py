from setuptools import setup  # type: ignore

setup(
    name="reexecution",
    version="dev",
    description="Dagster example for re-executing a pipeline.",
    author="Elementl",
    author_email="hello@elementl.com",
    packages=["reexecution"],  # same as name
    license="Apache-2.0",
    url="https://github.com/dagster-io/dagster/tree/master/examples/reexecution",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    extras_require={"test": ["pandas", "pyarrow; python_version < '3.9'", "pyspark"]},
)
