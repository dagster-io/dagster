import importlib.metadata

__version__ = importlib.metadata.version(__package__ or __name__)
from sphinx.application import Sphinx


def setup(app: Sphinx):
    from sphinxcontrib.mdxbuilder.builders.mdx import MdxBuilder

    app.add_builder(MdxBuilder)

    # File suffix for generated files
    app.add_config_value("mdx_file_suffix", ".mdx", "env")
    # Suffix for internal links, blank by default, e.g. '/path/to/file'
    # Add .mdx to get '/path/to/file.mdx'
    app.add_config_value("mdx_link_suffix", None, "env")

    # File transform function for filenames, by default returns docname + mdx_file_suffix
    app.add_config_value("mdx_file_transform", None, "env")

    # Link transform function for links, by default returns docname + mdx_link_suffix
    app.add_config_value("mdx_link_transform", None, "env")

    app.add_config_value("mdx_max_line_width", 120, "env")

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
