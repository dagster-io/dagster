# For a full of config options see:
#   https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# We add two kinds of packages to `sys.path`:
# 
# - Targets for `autodoc` (referenced via e.g. `automodule` in our doc source rst files).
#   `autodoc` runs in python and actually imports its targets, so they must be available on
#   `sys.path`.
# - Custom sphinx extensions (autodoc_configurable).

import os
import sys

# https://github.com/click-contrib/sphinx-click/issues/86

paths = [
    ### dagster packages
    "../../python_modules/automation",
    "../../python_modules/dagster",
    "../../python_modules/dagster-graphql",
    "../../python_modules/dagit",
    "../../python_modules/libraries/dagster-airbyte",
    "../../python_modules/libraries/dagster-airflow",
    "../../python_modules/libraries/dagster-aws",
    "../../python_modules/libraries/dagster-azure",
    "../../python_modules/libraries/dagster-celery",
    "../../python_modules/libraries/dagster-celery-docker",
    "../../python_modules/libraries/dagster-dask",
    "../../python_modules/libraries/dagster-datadog",
    "../../python_modules/libraries/dagster-datahub",
    "../../python_modules/libraries/dagster-docker",
    "../../python_modules/libraries/dagster-fivetran",
    "../../python_modules/libraries/dagster-github",
    "../../python_modules/libraries/dagster-k8s",
    "../../python_modules/libraries/dagster-mlflow",
    "../../python_modules/libraries/dagster-msteams",
    "../../python_modules/libraries/dagster-mysql",
    "../../python_modules/libraries/dagster-pagerduty",
    "../../python_modules/libraries/dagster-pandas",
    "../../python_modules/libraries/dagster-papertrail",
    "../../python_modules/libraries/dagster-postgres",
    "../../python_modules/libraries/dagster-prometheus",
    "../../python_modules/libraries/dagster-shell",
    "../../python_modules/libraries/dagster-slack",
    "../../python_modules/libraries/dagster-snowflake",
    "../../python_modules/libraries/dagster-snowflake-pandas",
    "../../python_modules/libraries/dagster-spark",
    "../../python_modules/libraries/dagster-ssh",
    "../../python_modules/libraries/dagster-twilio",
    "../../python_modules/libraries/dagstermill",
    "../../python_modules/libraries/dagster-celery-k8s",
    "../../python_modules/libraries/dagster-dbt",
    "../../python_modules/libraries/dagster-ge",
    "../../python_modules/libraries/dagster-gcp",
    "../../python_modules/libraries/dagster-pyspark",
    "../../python_modules/libraries/dagster-databricks",

    ### autodoc_configurable extension
    "./_ext",

]

for path in paths:
    sys.path.insert(0, os.path.abspath(path))

# -- Project information -----------------------------------------------------

project = 'Dagster'
copyright = '2019, Elementl, Inc'  # pylint: disable=redefined-builtin
author = 'The Dagster Team'

# The short X.Y version
version = ""
# The full version, including alpha/beta/rc tags
release = ""

# -- General configuration ---------------------------------------------------

# NOTE: `sphinx.ext.*` extensions are built-in to sphinx-- all others are supplied by other
# packages. Docs for all builtin extensions here:
#   https://www.sphinx-doc.org/en/master/usage/extensions/index.html
extensions = [
    # Automatically generate docs from docstrings.
    "sphinx.ext.autodoc",

    # Allows direct references to doc sections by title
    "sphinx.ext.autosectionlabel",

    # Conditionally build sections of docs
    "sphinx.ext.ifconfig",

    # Supplements autodoc with the ability to parse numpy and google-style docstrings (dagster
    # uses google style).
    "sphinx.ext.napoleon",

    # Adds links to source code for autodoc objects
    "sphinx.ext.viewcode",

    # Directives for automatically documenting CLIS built with the `click` package.
    "sphinx_click.ext",

    # Elementl-authored extension with custom directives and sphinx processing.
    "autodoc_dagster",

    # Renders a collapsible HTML component. Used by autodoc_dagster.
    "sphinx_toolbox.collapse",
]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# List of all packages that should be mocked when autodoc is running. Autodoc is going to import
# dagster packages, which in turn import various third-party packages. The vast majority of those
# packages are not actually needed to build the docs, but autodoc will nonetheless choke if it can't
# resolve their imports. By mocking them, we let autodoc do its work while keeping the build
# environment simple. If a build fails due to a failed import, try adding the root package for that
# import (e.g. `foo` for `foo.bar`) here.
autodoc_mock_imports = [
    "airflow",
    "azure",
    "celery",
    "coloredlogs",
    "croniter",
    "dask",
    "databricks_api",
    "datadog",
    "docker",
    "docker_image",
    "gevent",
    "great_expectations",
    "graphql",
    "grpc_health",
    "gql",
    "jwt",
    "kombu",
    "kubernetes",
    "lazy_object_proxy",
    "mlflow",
    "mysql",
    "oauth2client",
    "pep562",
    "prometheus_client",
    "psycopg2",
    "pypd",
    "slack_sdk",
    "snowflake",
    "sshtunnel",
    "toposort",
    "twilio",
    "typing_compat",
    "yaml",
]

# ????
autodoc_typehints = "none"

# From https://www.sphinx-doc.org/en/master/usage/extensions/autosectionlabel.html#confval-autosectionlabel_prefix_document
#   "Prefix each section label with the name of the document it is in, followed by a colon. For
#   example, index:Introduction for a section called Introduction that appears in document index.rst.
#   Useful for avoiding ambiguity when the same section heading appears in different documents."
autosectionlabel_prefix_document = True
