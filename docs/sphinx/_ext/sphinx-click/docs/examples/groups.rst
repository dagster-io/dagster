Documenting groups
==================

Consider the following sample application, using |Group|_:

.. literalinclude:: ../../examples/groups/cli.py

This can be documented using *sphinx-click* like so:

.. code-block:: rst

   .. click:: groups.cli:cli
     :prog: cli
     :nested: full

The rendered example is shown below.

----

.. click:: groups.cli:cli
  :prog: cli
  :nested: full

.. |Group| replace:: ``Groups``
.. _Group: https://click.palletsprojects.com/en/7.x/api/#click.Group
