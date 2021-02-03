import setuptools

setuptools.setup(
    name="{{ repo_name }}",
    install_requires=[
        "dagster==0.10.2",
        "dagit==0.10.2",
        "pytest",
    ],
)
