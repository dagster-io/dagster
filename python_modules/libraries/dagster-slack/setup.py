from setuptools import find_packages, setup


def get_version():
    version = {}
    with open("dagster_slack/version.py") as fp:
        exec(fp.read(), version)  # pylint: disable=W0122

    return version["__version__"]


if __name__ == "__main__":
    setup(
        name="dagster-slack",
        version=get_version(),
        author="Elementl",
        author_email="hello@elementl.com",
        license="Apache-2.0",
        description="A Slack client resource for posting to Slack",
        url="https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-slack",
        classifiers=[
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "License :: OSI Approved :: Apache Software License",
            "Operating System :: OS Independent",
        ],
        packages=find_packages(exclude=["test"]),
        install_requires=[
            "dagster",
            # Slack 2.x does not support Python 2
            # https://github.com/slackapi/python-slackclient/wiki/Migrating-to-2.x#minimum-python-versions
            "slackclient<2.0.0",
        ],
        zip_safe=False,
    )
