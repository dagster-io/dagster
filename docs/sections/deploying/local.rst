.. _local-dagit:

Running Dagit as a service
--------------------------

The core of any deployment of Dagster is a Dagit process that serves a user interface and responds
to GraphQL queries.

Ensure that you are running a recent Python version (Dagster is tested on Python 2.7, 3.5, 3.6, 3.7,
and 3.8). Typically, you'll want to run Dagit inside a
`virtualenv <https://virtualenv.pypa.io/en/stable/>`_. Then, you can install Dagit and any
additional libraries you might need.

.. code-block:: shell

    $ pip install dagit

To run Dagit, you'll use a command such as the following:

.. code-block:: shell

    $ DAGSTER_HOME=/opt/dagster/dagster_home dagit -h 0.0.0.0 -p 3000

In this configuration, Dagit will write execution logs to ``$DAGSTER_HOME/logs`` and listen on
`0.0.0.0:3000`.

Using systemd
~~~~~~~~~~~~~

To run Dagit as a long-lived service, you can install a systemd service such as the following:

.. literalinclude:: systemd/dagit.service
  :caption: dagit.service

Note that this assumes you've got a virtualenv for Dagster at ``/opt/dagster/venv`` and that your
pipeline code and ``repository.yaml`` are located under ``/opt/dagster/app``.

Dagit in Docker
~~~~~~~~~~~~~~~

If you are running on AWS ECS, Kubernetes, or some other container-based orchestration system,
you'll likely want to package Dagit using a Docker image.

A minimal skeleton ``Dockerfile`` and entrypoint shell script that will run Dagit and the cron
scheduler are shown below:

.. literalinclude:: docker/Dockerfile
  :caption: Dockerfile

In this setup, the contents of ``entrypoint.sh`` should be something like the following. This
script ensures that cron will run in the Docker container alongside Dagit:

.. literalinclude:: docker/entrypoint.sh
  :caption: entrypoint.sh

In practice, you may want to volume your pipeline code into your containers to enable deployment
patterns such as git-sync sidecars that avoid the need to rebuild images and redeploy containers
when pipeline code changes.

Dagit servers expose a health check endpoint at ``/dagit_info``, which returns a JSON response like:

.. code-block:: JSON

    {
      "dagit_version": "0.6.6",
      "dagster_graphql_version": "0.6.6",
      "dagster_version": "0.6.6"
    }

Depending on your deployment philosophy, you may want to run dagit as a service within your
container, use healthchecks as part of a container restart policy, or both.
