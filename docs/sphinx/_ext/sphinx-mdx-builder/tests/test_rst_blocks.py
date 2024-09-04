import os

import pytest

from sphinx.application import Sphinx

default_config = {
    "extensions": ["sphinxcontrib.mdxbuilder"],
    "master_doc": "index",
}


@pytest.fixture(scope="module")
def sphinx_build(tmp_path_factory):
    src_dir = os.path.dirname(__file__)
    output_dir = tmp_path_factory.mktemp("output")
    app = Sphinx(
        srcdir=src_dir + "/datasets",
        confdir=src_dir,
        outdir=str(output_dir / "datasets"),
        doctreedir=str(output_dir / "doctrees"),
        buildername="mdx",
        confoverrides=default_config,
    )
    app.build(force_all=True, filenames=["index.rst"])

    return output_dir


def test_mdx_builder(sphinx_build):
    expected_files = [
        "index.mdx",
        # Add other expected .mdx files here
    ]

    for file in expected_files:
        expected_file = sphinx_build / "datasets" / file
        assert expected_file.exists(), f"{expected_file} was not generated"

    # Optionally, check the content of the generated files
    with open(sphinx_build / "datasets" / "index.mdx", "r") as f:
        content = f.read()
        assert "This folder contains test sources." in content
