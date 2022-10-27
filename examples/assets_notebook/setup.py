from setuptools import find_packages, setup

setup(
    name="assets_notebook",
    packages=find_packages(exclude=["assets_notebook_tests"]),
    install_requires=[
        "dagster",
        "dagstermill",
        "papermill-origami",
        "pandas",
        "numpy",
        "sklearn",
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
