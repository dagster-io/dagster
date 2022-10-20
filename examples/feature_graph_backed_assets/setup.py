from setuptools import find_packages, setup

setup(
    name="feature_graph_backed_assets",
    packages=find_packages(exclude=["feature_graph_backed_assets_tests"]),
    install_requires=["dagster", "pandas"],
    license="Apache-2.0",
    description="Dagster example of op and graph-backed assets.",
    url="https://github.com/dagster-io/dagster/tree/master/examples/feature_graph_backed_assets",
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
