Documenting command collections
===============================

Consider the following sample application, using |CommandCollection|_:

.. literalinclude:: ../../examples/commandcollections/cli.py

This can be documented using *sphinx-click* like so:

.. code-block:: rst

   .. click:: commandcollections.cli:cli
     :prog: cli
     :nested: full

The rendered example is shown below.

----

.. click:: commandcollections.cli:cli
  :prog: cli
  :nested: full

.. |CommandCollection| replace:: ``CommandCollection``
.. _CommandCollection: https://click.palletsprojects.com/en/7.x/api/#click.CommandCollection
