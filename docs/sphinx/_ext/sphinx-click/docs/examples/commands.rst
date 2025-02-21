Documenting commands
====================

Consider the following sample application, using |Command|_:

.. literalinclude:: ../../examples/commands/cli.py

This can be documented using *sphinx-click* like so:

.. code-block:: rst

   .. click:: commands.cli:cli
     :prog: cli
     :nested: full

The rendered example is shown below.

----

.. click:: commands.cli:cli
  :prog: cli
  :nested: full

.. |Command| replace:: ``Command``
.. _Command: https://click.palletsprojects.com/en/7.x/api/#click.Command
