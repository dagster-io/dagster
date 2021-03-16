import setuptools

setuptools.setup(
    name="{{ repo_name }}",
    packages=setuptools.find_packages(exclude=["{{ repo_name }}_tests"]),
    install_requires=[
        "dagster==0.10.2",
        "dagit==0.10.2",
        "pytest",
    ],
)
