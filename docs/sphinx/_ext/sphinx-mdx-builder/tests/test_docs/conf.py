"""Sphinx configuration for testing sphinx-mdx-builder."""

import os
import sys

# Add the parent directory to the path so we can import our extension
sys.path.insert(0, os.path.abspath("../.."))
sys.path.insert(0, os.path.abspath(".."))

# Project information
project = "Test Project"
copyright = "2024, Test Author"  # noqa: A001
author = "Test Author"
release = "1.0.0"

# General configuration
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinxcontrib.mdxbuilder",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Options for HTML output
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# Options for autodoc
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

# MDX builder configuration
mdx_file_suffix = ".mdx"
mdx_link_suffix = ""
mdx_max_line_width = 120
mdx_title_suffix = " | Test Docs"
mdx_description_meta = "Generated test documentation"
mdx_github_url = "https://github.com/test/test-repo/blob/main"
mdx_show_source_links = True
