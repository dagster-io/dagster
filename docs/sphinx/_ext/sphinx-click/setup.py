#!/usr/bin/env python3

from setuptools import find_packages, setup

setup(
    name="sphinx-click",
    version="0.0.1",
    description="Sphinx extension that automatically documents click applications",
    long_description_content_type="text/x-rst; charset=UTF-8",
    author="Stephen Finucane",
    author_email="stephen@that.guru",
    url="https://github.com/click-contrib/sphinx-click",
    project_urls={
        "Bug Tracker": "https://github.com/click-contrib/sphinx-click/issues",
        "Documentation": "https://sphinx-click.readthedocs.io/en/latest",
        "Source Code": "https://github.com/click-contrib/sphinx-click",
    },
    license="MIT License",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Framework :: Sphinx :: Extension",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Documentation",
        "Topic :: Documentation :: Sphinx",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    keywords="sphinx click",
    packages=find_packages(),
)
