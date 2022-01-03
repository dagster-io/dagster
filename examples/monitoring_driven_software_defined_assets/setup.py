from setuptools import setup  # type: ignore

setup(
    name="consumption_datamart",
    version="dev",
    author_email="david@davidlaing.com",
    packages=["consumption_datamart"],  # same as name
    install_requires=[
        'dagster',
        'dagit',
        'SQLAlchemy',
        'pandas'
    ],
    extras_require={"test": ["pytest"]},
    author="Elementl",
    license="Apache-2.0",
    description="Example showing how to test drive the creation of a Data Mart focussed on consumption for software products",
    url="https://github.com/dagster-io/dagster/tree/master/examples/test_driven_software_defined_assets",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ]
)
