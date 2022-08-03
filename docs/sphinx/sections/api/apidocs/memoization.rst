Versioning and Memoization (Experimental)
=========================================

Dagster allows for code versioning and memoization of previous outputs based upon that versioning.
Listed here are APIs related to versioning and memoization.

.. currentmodule:: dagster

Versioning
----------
.. currentmodule:: dagster

.. autoclass:: VersionStrategy
    :members:

.. autoclass:: SourceHashVersionStrategy

.. autoclass:: OpVersionContext

.. autoclass:: ResourceVersionContext

Memoization
-----------
.. currentmodule:: dagster

.. autoclass:: MemoizableIOManager
    :members:

See also: :py:class:`dagster.IOManager`.

.. attribute:: MEMOIZED_RUN_TAG

    Provide this tag to a run to toggle memoization on or off. ``{MEMOIZED_RUN_TAG: "true"}`` toggles memoization on, while ``{MEMOIZED_RUN_TAG: "false"}`` toggles memoization off.
