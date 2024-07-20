Jobs
====

A ``Job`` binds a ``Graph`` and the resources it needs to be executable.

.. currentmodule:: dagster

You can create Jobs by calling :py:meth:`GraphDefinition.to_job` on a graph instance or using the :py:class:`job` decorator.

.. autodecorator:: job

.. autoclass:: JobDefinition

Reconstructable jobs
-------------------------
.. autoclass:: reconstructable
   :noindex:

.. autofunction:: build_reconstructable_job