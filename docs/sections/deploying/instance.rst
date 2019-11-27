.. _instance:

Configuring an instance
-----------------------

A Dagster instance is composed of:

- Event Log Storage: Stores the record of structured events produced during runs. Ideally
  implementations allow for monitoring the event log in some capacity to enable real time
  monitoring via Dagit.

- Run Storage: Used to keep track of runs over time and query select subsets of them. Separate
  from the event log store to allow for efficient queries of run history.

- Compute Log Manager: Makes available copies of stdout and stderr on a per execution step basis
  for debugging. This includes a real time subscription component as well as optional hooks for
  storage.

- Local Artifact Storage: This ensures that a singular directory is used for all the file system
  artifacts produced by Dagster. This is useful for both sharing intermediates across multiple
  executions or simply to provide a single point of audit.

Tools like the Dagster CLI or Dagit use the following behavior to select the current instance:

1. Use the explicit settings in `$DAGSTER_HOME/dagster.yaml` if they exist
2. Create a local instance rooted at `$DAGSTER_HOME` if it is set
3. Create a local instance in the fallback directory if provided (used by dagit to maintain history
   between restarts)
4. Use an ephemeral instance, which will hold information in memory and use a TemporaryDirectory
   for local artifacts which is cleaned up on exit. This is useful for tests and is the default
   for direct python api invocations such as `execute_pipeline`.


Writing a dagster.yaml
^^^^^^^^^^^^^^^^^^^^^^

You can use the explicit settings in ``$DAGSTER_HOME/dagster.yaml`` to tell Dagster which classes
to use to manage the event log storage, run log storage, and so forth. This means that these
storage classes are pluggable.

In general, you can tell Dagster which class to use for, e.g., run storage by writing yaml like:

.. code-block:: YAML

    run_storage:
      module: my_very_awesome_module.run_storage
      class: AwesomeRunStorage
      config:
        secret_word: "quux"

(If you're thinking of writing your own class for a case like this, please get in touch -- we can
help you implement the necessary interfaces.)

Using a local or remote Postgres instance for storage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We've written a set of classes (in ``dagster-postgres``) which let you target a (local or remote)
Postgres instance to store information about runs and event logs.

Make sure that ``dagster-postgres`` is installed in your Python environment, put the following lines
into your ``dagster.yaml`` (replacing the values for ``user``, ``password``, the port, and
``db_name`` as needed to target your own local or remote Postgres instance), and then just start
dagit as normal:

.. code-block:: YAML

    run_storage:
      module: dagster_postgres.run_storage
      class: PostgresRunStorage
      config:
        postgres_url: "postgresql://user:password@instance.us-west-1.rds.amazonaws.com:5432/db_name"

    event_log_storage:
      module: dagster_postgres.event_log
      class: PostgresEventLogStorage
      config:
        postgres_url: "postgresql://user:password@instance.us-west-1.rds.amazonaws.com:5432/db_name"
