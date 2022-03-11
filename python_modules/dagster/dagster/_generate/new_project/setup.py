import setuptools

setuptools.setup(
    name="{{ repo_name }}",
    packages=setuptools.find_packages(exclude=["{{ repo_name }}_tests"]),
    install_requires=[
        "dagster=={{ dagster_version }}",
        "dagit=={{ dagster_version }}",
        "pytest",
    ],
)
