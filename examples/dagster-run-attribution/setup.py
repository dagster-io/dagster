from setuptools import setup  # type: ignore

setup(
    name="run_attribution_example",
    version="dev",
    author_email="hello@elementl.com",
    packages=["run_attribution_example"],  # same as name
    install_requires=["dagster", "flask"],  # external packages as dependencies
    author="Elementl",
    license="Apache-2.0",
    description="Dagster example for performing run attribution by reading from HTTP headers in the RunCoordinator",
    url="https://github.com/dagster-io/dagster/tree/master/examples/dagster-run-attribution",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    extras_require={"test": ["pytest", "mock"]},
)
