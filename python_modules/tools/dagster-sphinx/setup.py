from setuptools import find_packages, setup

setup(
    name="bollinger",
    version="0+dev",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-pandera",
        "jupyterlab",
        "matplotlib",
        "seaborn",
        "pandera",
        "pandas",
    ],
    extras_require={
        "test": ["dagster[test]"],
    },
)
