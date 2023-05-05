from setuptools import find_packages, setup

setup(
    name="assets_pandas_type_metadata",
    packages=find_packages(exclude=["assets_pandas_type_metadata_tests"]),
    install_requires=[
        "dagster",
        "dagster-pandera",
        "jupyterlab",
        "matplotlib",
        "seaborn",
        "pandera",
        "pandas<2",  # See: https://github.com/dagster-io/dagster/issues/13339
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
