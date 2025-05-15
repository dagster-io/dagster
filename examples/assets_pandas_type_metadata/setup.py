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
        "pandas",
        "pyarrow",
        "pandera<0.24.0",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
