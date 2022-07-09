from setuptools import setup  # type: ignore

setup(
    name="run_attribution_example",
    version="0+dev",
    author_email="hello@elementl.com",
    packages=["run_attribution_example"],  # same as name
    install_requires=["dagster"],  # external packages as dependencies
    author="Elementl",
    license="Apache-2.0",
    description="Dagster example for performing run attribution by reading from HTTP headers in the RunCoordinator",
    url="https://github.com/dagster-io/dagster/tree/master/examples/run_attribution_example",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    extras_require={"test": ["pytest", "mock"]},
    python_requires=">=3.6,<=3.10",
)
