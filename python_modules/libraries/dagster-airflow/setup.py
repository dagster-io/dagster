from setuptools import find_packages, setup


def get_version():
    version = {}
    with open("dagster_airflow/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    ver = get_version()
    setup(
        name="dagster-airflow",
        version=ver,
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="Airflow plugin for Dagster",
        url="https://github.com/dagster-io/dagster",
        classifiers=[
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["dagster_airflow_tests"]),
        install_requires=[
            "dagster=={ver}".format(ver=ver),
            "docker",
            "python-dateutil>=2.8.0",
            "lazy_object_proxy",
            "pendulum==1.4.4",
            # https://issues.apache.org/jira/browse/AIRFLOW-6854
            'typing_extensions; python_version>="3.8"',
        ],
        extras_require={"kubernetes": ["kubernetes>=3.0.0", "cryptography>=2.0.0"]},
        entry_points={"console_scripts": ["dagster-airflow = dagster_airflow.cli:main"]},
    )
