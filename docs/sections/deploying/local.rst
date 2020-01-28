.. _local-dagit:

Local or Standalone Dagit
-------------------------

The simplest way to deploy Dagster / Dagit is in standalone mode. You can deploy Dagit as a service
in your environment; some options for configuring this are described below.

.. rubric:: Run on a VM

To launch Dagit on a bare VM, ensure that you've got a recent Python version (preferably 3.7, but
2.7, 3.5, 3.6, and 3.7 are supported), and preferably a virtualenv configured. Then, you can install
Dagster and any libraries you need:

.. code-block:: shell

    $ virtualenv --python=/usr/bin/python3 /some/path/to/venv
    $ source /some/path/to/venv/bin/activate
    $ pip install dagster dagit dagster-aws # ... any other dagster libraries you need, e.g. dagster-bash

To run Dagit, you can run something like the following:

.. code-block:: shell

    $ DAGSTER_HOME=/set/a/dagster_home dagit -h 0.0.0.0 -p 3000

In this configuration, Dagit will write execution logs to ``$DAGSTER_HOME/logs`` and listen on port
3000. To run Dagit as a long-lived service on this host, you can install a systemd service similar
to the AWS quick start, with something like:

.. code-block::

    [Unit]
    Description=Run Dagit
    After=network.target

    [Service]
    Type=simple
    User=ubuntu
    ExecStart=/bin/bash -c '\
        export DAGSTER_HOME=/opt/dagster/dagster_home && \
        export PYTHONPATH=$PYTHONPATH:/opt/dagster/app && \
        export LC_ALL=C.UTF-8 && \
        export LANG=C.UTF-8 && \
        source /opt/dagster/venv/bin/activate && \
        /opt/dagster/venv/bin/dagit \
            -h 0.0.0.0 \
            -p 3000 \
            -y /opt/dagster/app/repository.yaml
    Restart=always
    WorkingDirectory=/opt/dagster/app/

    [Install]
    WantedBy=multi-user.target

Note that this assumes you've got a virtualenv for Dagster at ``/opt/dagster/venv`` and your client
code and ``repository.yaml`` are located at ``/opt/dagster/app``.

.. rubric:: Docker

If you are running on AWS ECS, Kubernetes, or some other container-based orchestration system,
you'll likely want to containerize Dagit using Docker.

A minimal skeleton ``Dockerfile`` and entrypoint shell script that will run Dagit and the cron
scheduler are shown below:

.. code-block:: Dockerfile

    :caption: Dockerfile

    FROM dagster:dagster-py37:latest

    RUN mkdir /opt/dagster/dagster_home

    WORKDIR /

    # COPY ## -> TODO: copy your Dagster client code here

    COPY entrypoint.sh .
    RUN chmod +x /entrypoint.sh

    EXPOSE 3000

    ENTRYPOINT ["/entrypoint.sh"]


You can do something like the following ``entrypoint.sh`` to ensure cron is running in the Docker
container alongside Dagit:

.. code-block:: shell

    :caption: entrypoint.sh

    #!/bin/sh

    # see: https://unix.stackexchange.com/a/453053 - fix link-count
    touch /etc/crontab /etc/cron.*/*

    service cron start

    export DAGSTER_HOME=/opt/dagster/dagster_home

    # Add all schedules
    /usr/local/bin/dagster schedule up

    # Restart previously running schedules
    /usr/local/bin/dagster schedule restart --restart-all-running


This ``Dockerfile`` is based on the `public Docker
images <https://cloud.docker.com/u/dagster/repository/docker/dagster/dagster>`_. We publish versions
for Python 2.7, 3.5, 3.6, and 3.7.
