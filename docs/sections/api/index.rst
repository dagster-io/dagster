API Docs
========

These docs aim to cover the entire public surface of the ``dagster`` APIs, as
well as, eventually, public APIs from all the associated libraries.

Dagster follows `SemVer <https://semver.org/>`_, and is currently pre-1.0. We
are attempting to isolate breaking changes to the public APIs to minor versions
(on a roughly 8-week cadence) and will announce deprecations in Slack and in
the release notes to patch versions (on a roughly weekly cadence).

.. rubric:: Core

APIs from the core ``dagster`` package are divided roughly by topic:

`Solids <apidocs/solids.html>`_
  APIs to define or decorate functions as solids, declare their inputs and
  outputs, compose solids with each other, as well as the datatypes that
  solid execution can return or yield.

`Pipelines <apidocs/pipeline.html>`_
  APIs to define pipelines, dependencies and fan-in dependencies between
  solids, and aliased instances of solids; pipeline modes, resources, loggers,
  presets, and repositories.

`Execution <apidocs/execution.html>`_
  APIs to execute and test pipelines and individual solids, the execution
  context available to solids, pipeline configuration, the default system
  storages used for intermediates, and the default executors available for
  executing pipelines.

`Types <apidocs/types.html>`_
  Primitive types available for the input and output values of solids, and the
  APIs used to define and test new Dagster types.

`Config <apidocs/config.html>`_
  The types available to describe config schemas.

`Schedules <apidocs/schedules.html>`_
  APIs to define schedules on which pipelines are run, as well as a
  few built-in defaults.

`Partitions <apidocs/partitions.html>`_
  APIs to define partitions of the config space over which pipeline runs can
  be backfilled.

`Errors <apidocs/errors.html>`_
  Errors thrown by the Dagster framework.

`Dagster CLI <apidocs/cli.html>`_
  Browse repositories and execute pipelines from the command line

`Utilities <apidocs/utilities.html>`_ 
  Miscellaneous helpers used by Dagster that may be useful to users.

`Internals <apidocs/internals.html>`_
  Core internal APIs that are important if you are interested in understanding
  how Dagster works with an eye towards extending it: logging, executors,
  system storage, the Dagster instance & plugin machinery, storage, schedulers.

.. rubric:: Libraries

.. include:: libraries.rst


.. toctree::
  :maxdepth: 2
  :name: API Reference
  :hidden:
  :includehidden:

  apidocs/solids
  apidocs/pipeline
  apidocs/execution
  apidocs/types
  apidocs/config
  apidocs/schedules
  apidocs/partitions
  apidocs/errors
  apidocs/cli
  apidocs/utilities

  apidocs/internals
  apidocs/libraries/index
