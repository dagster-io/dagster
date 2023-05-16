Job-Level Versioning and Memoization (Deprecated)
=================================================

Dagster has deprecated functionality that allows for job-level code versioning and memoization of previous op outputs based upon that versioning.

This is currently deprecated in favor of `asset versioning </concepts/assets/software-defined-assets#asset-code-versions>`_.

.. currentmodule:: dagster

Versioning
----------
.. currentmodule:: dagster

.. autoclass:: VersionStrategy

.. autoclass:: SourceHashVersionStrategy

.. autoclass:: OpVersionContext

.. autoclass:: ResourceVersionContext

Memoization
-----------
.. currentmodule:: dagster

.. autoclass:: MemoizableIOManager

See also: :py:class:`dagster.IOManager`.

.. attribute:: MEMOIZED_RUN_TAG

    Provide this tag to a run to toggle memoization on or off. ``{MEMOIZED_RUN_TAG: "true"}`` toggles memoization on, while ``{MEMOIZED_RUN_TAG: "false"}`` toggles memoization off.
