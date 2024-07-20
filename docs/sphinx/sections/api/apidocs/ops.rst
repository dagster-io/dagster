.. currentmodule:: dagster

Ops
===

The foundational unit of computation in Dagster.

-----

Op Definition
------------
.. autodecorator:: op

.. autoclass:: OpDefinition
    :members: configured

-------

Ins & outs
----------------

.. autoclass:: In

.. autoclass:: Out


-------

Execution
---------

.. autoclass:: RetryPolicy

.. autoclass:: Backoff

.. autoclass:: Jitter

-------

.. _events:

Events
------

Objects that ops' compute functions can yield to communicate with the Dagster framework.

(Note: raise :py:class:`Failure` and :py:class:`RetryRequested` from ops rather than yielding them.)

Event types
^^^^^^^^^^^

.. autoclass:: Output

.. autoclass:: AssetMaterialization

.. autoclass:: ExpectationResult

.. autoclass:: TypeCheck

.. autoclass:: Failure

.. autoclass:: RetryRequested