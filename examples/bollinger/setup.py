from setuptools import setup, find_packages

setup(
    name="bollinger",
    version="dev",
    packages=find_packages(),
    install_requires=[
        "dagster",
        "dagster-pandera",
        "matplotlib",
        "pandas",
        "seaborn",
        "jupyterlab",
    ],
    extras_require={
        "notebook": ["jupyterlab"],
    },
)
