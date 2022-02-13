from setuptools import setup, find_packages

setup(
    name="bollinger",
    version="dev",
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
)
