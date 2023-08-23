from setuptools import find_packages, setup

setup(
    name="dagster_university",
    packages=find_packages(exclude=["dagster_university_tests"]),
    install_requires=[
        "dagster==1.4.*",
        "dagster-cloud",
        "dagster-duckdb",
        "geopandas",
        "kaleido",
        "pandas",
        "plotly",
        "shapely",
        "kaleido==0.1"
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
