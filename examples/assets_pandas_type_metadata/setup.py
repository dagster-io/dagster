from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="assets_pandas_type_metadata",
        packages=find_packages(exclude=["assets_pandas_type_metadata_tests"]),
        install_requires=[
            "dagster",
            "dagit",
            "dagster-pandera",
            "jupyterlab",
            "matplotlib",
            "seaborn",
            "pandera",
            "pandas",
            "pytest",
        ],
    )
