import pickle

from docutils import nodes
from sphinx import addnodes as sphinx_nodes


def test_basics(make_app, rootdir):
    srcdir = rootdir / 'basics'
    app = make_app('xml', srcdir=srcdir)
    app.build()

    # TODO: rather than using the pickled doctree, we should decode the XML
    content = pickle.loads((app.doctreedir / 'index.doctree').read_bytes())

    # doc has format like so:
    #
    # document:
    #   section:
    #     title:
    #     section:
    #       title:
    #       paragraph:
    #       literal_block:
    #       rubric:
    #       index:
    #       desc:
    #         desc_signature:
    #         desc_signature:
    #       index:
    #       desc:
    #         desc_signature:
    #         desc_signature:

    section = content[0][1]
    assert isinstance(section, nodes.section)

    assert isinstance(section[0], nodes.title)
    assert section[0].astext() == 'greet'
    assert isinstance(section[1], nodes.paragraph)
    assert section[1].astext() == 'A sample command group.'
    assert isinstance(section[2], nodes.literal_block)

    assert isinstance(section[3], nodes.rubric)
    assert section[3].astext() == 'Commands'
    assert isinstance(section[4], sphinx_nodes.index)
    assert isinstance(section[5], sphinx_nodes.desc)
    assert section[5].astext() == 'hello\n\nGreet a user.'
    assert isinstance(section[6], sphinx_nodes.index)
    assert isinstance(section[7], sphinx_nodes.desc)
    assert section[7].astext() == 'world\n\nGreet the world.'


def test_commands(make_app, rootdir):
    srcdir = rootdir / 'commands'
    app = make_app('xml', srcdir=srcdir)
    app.build()

    # TODO: rather than using the pickled doctree, we should decode the XML
    content = pickle.loads((app.doctreedir / 'index.doctree').read_bytes())

    # doc has format like so:
    #
    # document:
    #   section:
    #     title:
    #     section:
    #       title:
    #       paragraph:
    #       literal_block:
    #       rubric:
    #       index:
    #       desc:
    #         desc_signature:
    #         desc_signature:

    section = content[0][1]
    assert isinstance(section, nodes.section)

    assert isinstance(section[0], nodes.title)
    assert section[0].astext() == 'greet'
    assert isinstance(section[1], nodes.paragraph)
    assert section[1].astext() == 'A sample command group.'
    assert isinstance(section[2], nodes.literal_block)

    # we should only show a single command, 'world'
    assert isinstance(section[3], nodes.rubric)
    assert section[3].astext() == 'Commands'
    assert isinstance(section[4], sphinx_nodes.index)
    assert isinstance(section[5], sphinx_nodes.desc)
    assert section[5].astext() == 'world\n\nGreet the world.'


def test_nested_full(make_app, rootdir):
    srcdir = rootdir / 'nested-full'
    app = make_app('xml', srcdir=srcdir)
    app.build()

    # TODO: rather than using the pickled doctree, we should decode the XML
    content = pickle.loads((app.doctreedir / 'index.doctree').read_bytes())

    # doc has format like so:
    #
    # document:
    #   section:
    #     title:
    #     section:
    #       title:
    #       paragraph:
    #       literal_block:
    #       section:
    #         title
    #         paragraph
    #         literal_block
    #         ...
    #       section:
    #         title
    #         paragraph
    #         literal_block

    section = content[0][1]
    assert isinstance(section, nodes.section)

    assert isinstance(section[0], nodes.title)
    assert section[0].astext() == 'greet'
    assert isinstance(section[1], nodes.paragraph)
    assert section[1].astext() == 'A sample command group.'
    assert isinstance(section[2], nodes.literal_block)

    subsection_a = section[3]
    assert isinstance(subsection_a, nodes.section)

    assert isinstance(subsection_a[0], nodes.title)
    assert subsection_a[0].astext() == 'hello'
    assert isinstance(subsection_a[1], nodes.paragraph)
    assert subsection_a[1].astext() == 'Greet a user.'
    assert isinstance(subsection_a[2], nodes.literal_block)
    # we don't need to verify the rest of this: that's done elsewhere

    subsection_b = section[4]
    assert isinstance(subsection_b, nodes.section)

    assert isinstance(subsection_b[0], nodes.title)
    assert subsection_b[0].astext() == 'world'
    assert isinstance(subsection_b[1], nodes.paragraph)
    assert subsection_b[1].astext() == 'Greet the world.'
    assert isinstance(subsection_b[2], nodes.literal_block)
