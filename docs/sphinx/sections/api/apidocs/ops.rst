.. currentmodule:: dagster

Ops
===

The foundational unit of computation in Dagster.

-----

Defining ops
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

The objects that can be yielded by the body of ops' compute functions to communicate with the
Dagster framework.

(Note that :py:class:`Failure` and :py:class:`RetryRequested` are intended to be raised from ops rather than yielded.)

Event types
^^^^^^^^^^^

.. autoclass:: Output

.. autoclass:: AssetMaterialization

.. autoclass:: ExpectationResult

.. autoclass:: TypeCheck

.. autoclass:: Failure

.. autoclass:: RetryRequested
