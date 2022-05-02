Types
=========

.. currentmodule:: dagster

Dagster includes facilities for typing the input and output values of ops ("runtime" types).

.. _builtin:

Built-in types
-------------------------

.. attribute:: Nothing

    Use this type only for inputs and outputs, in order to establish an execution dependency without
    communicating a value. Inputs of this type will not be passed to the op compute function, so
    it is necessary to use the explicit :py:class:`In` API to define them rather than
    the Python 3 type hint syntax.

    All values are considered to be instances of ``Nothing``.

    **Examples:**

    .. code-block:: python

        @op
        def wait(_) -> Nothing:
            time.sleep(1)
            return

        @op(
            ins={"ready": In(dagster_type=Nothing)},
        )
        def done(_) -> str:
            return 'done'

        @job
        def nothing_job():
            done(wait())

        # Any value will pass the type check for Nothing
        @op
        def wait_int(_) -> Int:
            time.sleep(1)
            return 1

        @job
        def nothing_int_job():
            done(wait_int())


.. autoclass:: FileHandle
   :members:

.. autoclass:: LocalFileHandle

Making New Types
----------------

.. autoclass:: DagsterType

.. autofunction:: PythonObjectDagsterType

.. autofunction:: dagster_type_loader

.. autoclass:: DagsterTypeLoader

.. autofunction:: dagster_type_materializer

.. autoclass:: DagsterTypeMaterializer

.. autofunction:: usable_as_dagster_type

.. autofunction:: make_python_type_usable_as_dagster_type

Testing Types
^^^^^^^^^^^^^

.. autofunction:: check_dagster_type
