Architectural overview
----------------------

Dagster is a layered and pluggable system. It is possible to call the Dagster Python APIs directly
from your own code, to call the ``dagster`` CLI, to execute GraphQL queries against Dagster using
the ``dagster-graphql`` CLI, to run ``dagster-graphql`` in containers that can respond to GraphQL
queries, to run Dagit on a standalone basis, or to compile Dagster DAGs for scheduling and execution
on Airflow. Individual pipeline runs may be executed on pluggable execution engines, including local
or remote Dask clusters. Metadata from these executions can be streamed to pluggable local and
remote storage backends.

This allows substantial flexibility in your deployment strategies. For example, it is
possible to point a local instance of Dagit, running on an individual developer's machine, at the
cloud storage being used by pipelines scheduled in production in order to inspect intermediate
artifacts.

Execution
~~~~~~~~~

Dagster pipelines can be executed in a single process, in multiple processes, or on a variety of
distributed compute platforms, by selecting between available executors at pipeline execution time
using config. This makes it possible to run a pipeline locally in a single process and then remote
on a production cluster just by switching config settings in Dagit or in the environment dict
provided to the Python API.

Dagster includes out-of-the-box support for local execution in a single process and in multiple
processes with the :py:data:`~dagster.in_process_executor` and
:py:data:`~dagster.multiprocess_executor`. These executors work well for pipelines of moderate
size or if your solids communicate with external systems or clusters (e.g., EMR or Dataproc) to
run heavy compute workloads.

These executors are available by default when executing a pipeline using any
:py:class:`~dagster.ModeDefinition` that does not define its own executors. By default, in the
absence of specific executor config, the in-process executor will be used. To select the
multiprocess executor, add a fragment like the following to the config of any pipeline:

.. code-block:: yaml

    execution:
      multiprocess:
        max_concurrent: 4
    storage:
      filesystem:

Note that a persistent system storage, such as the filesystem storage, must be configured in order
to make multiprocess execution available. This persistent system storage is used to pass
intermediate values between solids, and incidentally makes reexecution available for all
multiprocess executions.

The `dagster-dask <https://github.com/dagster-io/dagster/tree/master/python_modules/dagster-dask>`__
module makes a :py:data:`~dagster_dask.dask_executor` available, which can target either a local
Dask cluster or a distributed cluster. Computation is distributed across the cluster at the
execution step level. This is a straightforward path to testable and scalable distributed
execution for heavier workloads.

As with the multiprocess executor, a persistent system storage must be configured for Dask
execution.

Users can also write their own executors, which can be passed to the ``executor_defs`` argument on
:py:class:`~dagster.ModeDefinition`. If you're considering doing this, please reach out through our
Slack channel so that we can provide guidance and support.

Scheduling
~~~~~~~~~~

Dagster's approach to scheduling pipelines for periodic execution is also oriented toward
extensibility. Schedules are defined in code using the :py:func:`@schedules <dagster.schedules>`
API and may be executed by multiple concrete schedulers.

The first scheduler we've built is in the
`dagster-cron <https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-cron>`__
package and is backed by system cron, the :py:class:`~dagster_cron.SystemCronScheduler`. (See the
`tutorial docs <scheduling-pipeline-runs>`_ for an example of how to schedule pipeline executions
using the cron-backed scheduler.)

Users can also write their own schedulers. If you're considering doing this, please reach out
through our Slack channel so that we can provide guidance and support.

Compiling a pipeline for execution by a third-party scheduler
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It's also possible to schedule pipelines for execution by compiling them to a format that can be
understood by a third-party scheduling system, and then defining schedules within that system.

This is the approach we use to deploy Dagster pipelines to Airflow (using the
`dagster-airflow <https://github.com/dagster-io/dagster/tree/master/python_modules/dagster-airflow>`__
package).

A Dagster pipeline is first compiled with a set of config options into an execution plan,
and then the individual execution steps are expressed as Airflow tasks using a set of custom wrapper
operators. The resulting DAG can be deployed to an existing Airflow install and scheduled and
monitored using all the tools being used to existing pipelines (See the
`Airflow guide <deploying-to-airflow>`_ for details.)

If you're thinking of building a similar integration to target another third-party scheduler, please
reach out through our Slack channel so that we can provide guidance and support.


Storage
~~~~~~~

The Dagster tools are built so that the storage backends they use can be easily swapped. This makes
it easy to swap S3 for GCP (or cloud storage for local) or Postgres for MySQL, guarding against
lock-in and ensuring compatibility with a wide range of heterogeneous infrastructures. It also
makes some neat things possible. For example, a user running a local Dagit can point it at remote
storage backends in order to debug or monitor runs being executed on production infrastructure.

The DagsterInstance
^^^^^^^^^^^^^^^^^^^

The :py:class:`~dagster.core.instance.DagsterInstance` organizes all of the information specific to
a particular installation or deployment of Dagster. (Locally, this usually means a particular Dagit
process.)

An instance controls the collection of systems that are used by Dagster for persisting
deployment-wide information: the history of past runs, the log of structured events created by
those runs, the raw stdout and stderr streams created by those runs, and configuration for the local
storage of intermediates.

These systems are swappable in config, and users can write their own classes to handle persistence
of any or all of this data. See the `instance guide <configuring-an-instance>`_ for details on
how to configure and customize the instance. (As always, if you're interested in extending Dagster,
please reach out to us.)

System storage for intermediate artifacts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Intermediate persistence is configurable on a per-pipeline run basis. This is so that you can run
pure in-memory tests which don't persist anything, local runs that persist artifacts to disk for
debugging and inspection, and production runs that persist to permanent cloud storage for audit and
reproducibility.

Intermediate persistence is governed by subclasses of :py:class:`~dagster.SystemStorageDefinition`,
which can be attached to a :py:class:`~dagster.ModeDefinition`. By default, the 
