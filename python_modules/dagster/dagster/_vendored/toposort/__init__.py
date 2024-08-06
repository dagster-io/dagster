## Vendored toposort module

"""Vendored from https://gitlab.com/ericvsmith/toposort/-/blob/master/src/toposort.py?ref_type=heads on 2024-05-30.

pyproject.toml at time of vendoring:

[build-system]
requires = [
    "setuptools>=42",
    "wheel",
]
build-backend = "setuptools.build_meta"

[project]
name = "toposort"
requires-python = ">=3.6"
authors = [
    {name = "Eric V. Smith", email = "eric@trueblade.com"},
]
license = {text = "Apache License Version 2.0"}
description = "Implements a topological sort algorithm."
readme = {file = "README.md", content-type = "text/markdown"}
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
]
dynamic = ["version"]

[project.urls]
source = "https://gitlab.com/ericvsmith/toposort"

[tool.setuptools.dynamic]
# See https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html#dynamic-metadata
version = {attr = "toposort.__version__"}
"""
