# For a full of config options see:
#   https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# We add two kinds of packages to `sys.path`:
#
# - Targets for `autodoc` (referenced via e.g. `automodule` in our doc source rst files).
#   `autodoc` runs in python and actually imports its targets, so they must be available on
#   `sys.path`.
# - Custom sphinx extensions (autodoc_dagster).

import os
import sys

ignored_folders = ["dagster-test"]
base_path = "../../python_modules"
python_modules_path = os.path.abspath(base_path)
libraries_path = os.path.abspath(os.path.join(base_path, "libraries"))
paths = []
# Add python_modules folders
for folder in os.listdir(python_modules_path):
    folder_path = os.path.join(python_modules_path, folder)
    if os.path.isdir(folder_path) and not any(
        ignored in folder_path for ignored in ignored_folders
    ):
        paths.append(folder_path)
# Add libraries folders
for folder in os.listdir(libraries_path):
    folder_path = os.path.join(libraries_path, folder)
    if os.path.isdir(folder_path) and not any(
        ignored in folder_path for ignored in ignored_folders
    ):
        paths.append(folder_path)
# Add the _ext folder
paths.append(os.path.abspath("./_ext"))

for path in paths:
    sys.path.insert(0, path)
# -- Project information -----------------------------------------------------

project = "Dagster"
copyright = "2019, Dagster Labs, Inc"  # noqa: A001
author = "Dagster Labs"

# -- General configuration ---------------------------------------------------

# NOTE: `sphinx.ext.*` extensions are built-in to sphinx-- all others are supplied by other
# packages. Docs for all builtin extensions here:
#   https://www.sphinx-doc.org/en/master/usage/extensions/index.html
extensions = [
    # Automatically generate docs from docstrings.
    "sphinx.ext.autodoc",
    # Allows direct references to doc sections by title
    "sphinx.ext.autosectionlabel",
    # Supplements autodoc with the ability to parse numpy and google-style docstrings (dagster
    # uses google style).
    "sphinx.ext.napoleon",
    # Adds links to source code for autodoc objects
    "sphinx.ext.viewcode",
    # Directives for automatically documenting CLIs built with the `click` package.
    "sphinx_click.ext",
    # Dagster-labs-authored extension with custom directives and sphinx processing.
    "dagster_sphinx",
    "sphinx_toolbox.collapse",
    # Render MDX
    "sphinxcontrib.mdxbuilder",
]

# -- Extension configuration -------------------------------------------------

# -- autodoc

# Full list of options here:
#   https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html


# Include members (e.g. methods on classes) for all objects rendered with auto* methods by default.
# Without this, no methods will be rendered unless `:members:` is explicitly set on an individual
# directive invocation. Note that filtration by publicity (done in the `autodoc_dagster` extension)
# is performed on the member list controlled by this option-- without `members` set, even a method
# marked `@public` will _not_ be included in the docs!
autodoc_default_options = {"members": True, "undoc-members": True}

# Determines the order in which members (e.g., methods, attributes) are documented
# within a class or module. "groupwise" groups members by type (e.g., methods together,
# attributes together) before sorting alphabetically within each group.
autodoc_member_order = "groupwise"

# List of all packages that should be mocked when autodoc is running. Autodoc is going to import
# dagster packages, which in turn import various third-party packages. The vast majority of those
# packages are not actually needed to build the docs, but autodoc will nonetheless choke if it can't
# resolve their imports. By mocking them, we let autodoc do its work while keeping the build
# environment simple. If a build fails due to a failed import, try adding the root package for that
# import (e.g. `foo` for `foo.bar`) here. See `docs/README.md` for more details.
autodoc_mock_imports = [
    "airflow",
    "azure",
    "coloredlogs",
    "croniter",
    "dask",
    "databricks",
    "databricks_api",
    "databricks_cli",
    "datadog",
    "dlt",
    "docker",
    "docker_image",
    "gevent",
    "great_expectations",
    "grpc_health",
    "jwt",
    "kombu",
    "kubernetes",
    "lazy_object_proxy",
    "looker_sdk",
    "mlflow",
    "mypy_boto3_glue",
    "mysql",
    "oauth2client",
    "origami",
    "orjson",
    "pandas_gbq",
    "pandera",
    "polars",
    "prometheus_client",
    "psycopg2",
    "pypd",
    "sentry_sdk",
    "slack_sdk",
    "snowflake",
    "sshtunnel",
    "toposort",
    "twilio",
    "wandb",
]

autodoc_typehints = "none"

# From https://www.sphinx-doc.org/en/master/usage/extensions/autosectionlabel.html#confval-autosectionlabel_prefix_document
#   "Prefix each section label with the name of the document it is in, followed by a colon. For
#   example, index:Introduction for a section called Introduction that appears in document index.rst.
#   Useful for avoiding ambiguity when the same section heading appears in different documents."
autosectionlabel_prefix_document = True

# Only support Google-style docstrings
napoleon_numpy_docstring = False
