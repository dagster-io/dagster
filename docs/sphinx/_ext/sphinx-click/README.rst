============
sphinx-click
============

.. image:: https://github.com/click-contrib/sphinx-click/actions/workflows/ci.yaml/badge.svg
    :target: https://github.com/click-contrib/sphinx-click/actions/workflows/ci.yaml
    :alt: Build Status

.. image:: https://readthedocs.org/projects/sphinx-click/badge/?version=latest
    :target: https://sphinx-click.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

``sphinx-click`` is a `Sphinx`__ plugin that allows you to automatically extract
documentation from a `Click-based`__ application and include it in your docs.

__ http://www.sphinx-doc.org/
__ http://click.pocoo.org/

Installation
------------

Install the plugin using ``pip``:

.. code-block:: shell

   $ pip install sphinx-click

Alternatively, install from source by cloning this repo then running ``pip``
locally:

.. code-block:: shell

   $ pip install .

Usage
-----

.. important::

   To document a Click-based application, both the application itself and any
   additional dependencies required by that application **must be installed**.

Enable the plugin in your Sphinx ``conf.py`` file:

.. code-block:: python

   extensions = ['sphinx_click']

Once enabled, you can now use the plugin wherever necessary in the
documentation.

.. code-block::

   .. click:: module:parser
      :prog: hello-world
      :nested: full

Detailed information on the various options available is provided in the
`documentation <https://sphinx-click.readthedocs.io>`_.

Alternative
-----------

This plugin is perfect to document a Click-based CLI in Sphinx, as it properly
renders the help screen and its options in nice HTML with deep links and
styling.

However, if you are looking to document the source code of a Click-based CLI,
and the result of its execution, you might want to check out `click-extra`__.
The latter provides the ``.. click:example::`` and ``.. click:run::`` Sphinx
directives so you can `capture and render, with full colors, the result of your
CLI in your documentation`__.

__ https://github.com/kdeldycke/click-extra/
__ https://kdeldycke.github.io/click-extra/sphinx.html
