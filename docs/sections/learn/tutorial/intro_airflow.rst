Deploying to Airflow
--------------------

Although Dagster includes stand-alone functionality for
:ref:`executing <executing-our-first-pipeline>`, :ref:`scheduling <scheduler>`, and
:ref:`deploying pipelines on AWS <deployment-aws>`, we also support an incremental adoption
path on top of existing `Apache Airflow <https://airflow.apache.org/>`_ installs.

We've seen how Dagster compiles a logical pipeline definition, appropriately parameterized by config,
into a concrete execution plan for Dagster's execution engines. Dagster pipelines can also be
compiled into the DAG format used by Airflow -- or, in principle, to any other intermediate
representation used by a third-party scheduling or orchestration engine.

Let's see how to get our simple cereal pipeline to run on Airflow every morning before breakfast,
at 6:45 AM.

Requirements
^^^^^^^^^^^^
You'll need an existing Airflow installation, and to install the ``dagster-airflow`` library into
the Python environments in which your Airflow webserver and worker run:

.. code-block:: shell

    $ pip install dagster-airflow

You'll also need to make sure that the Dagster pipeline you want to run using Airflow is available
in the Python environments in which your Airflow webserver and worker run.

Scaffolding your pipeline for Airflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
We'll use our familiar, simple demo pipeline:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/airflow.py
   :linenos:
   :caption: airflow.py

To compile this existing pipeline to Airflow, we'll use the ``dagster-airflow`` CLI tool. By
default, this tool will write the Airflow-compatible DAG scaffold out to ``$AIRFLOW_HOME/dags``.

.. code-block:: shell

    $ dagster-airflow scaffold \
        --module-name dagster_examples.intro_tutorial.airflow \
        --pipeline-name hello_cereal_pipeline
    Wrote DAG scaffold to file: $AIRFLOW_HOME/dags/hello_cereal_pipeline.py

Let's take a look at the generated file:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/hello_cereal_pipeline.py
   :linenos:
   :caption: hello_cereal_pipeline.py

This is a fairly straightforward file with four parts.

First, we import the basic prerequisites to define our DAG (and also make sure that the string
"DAG" appears in the file, so that the Airflow webserver will detect it).

Second, we define the config that Dagster will compile our pipeline against. Unlike Dagster
pipelines, Airflow DAGs can't be parameterized dynamically at execution time, so this config is
static after it's loaded by the Airflow webserver.

Third, we set the ``DEFAULT_ARGS`` that will be passed down as the ``default_args`` argument to the
``airflow.DAG`` `constructor <https://airflow.apache.org/tutorial.html#example-pipeline-definition>`_.

Finally, we define the DAG and its constituent tasks using
:py:func:`make_airflow_dag <dagster_airflow.make_airflow_dag>`. If you run this code interactively,
you'll see that ``dag`` and ``tasks`` are ordinary Airflow objects, just as you'd expect to see
when defining an Airflow pipeline manually:

.. code-block:: python

    >>> dag
    <DAG: hello_cereal_pipeline>
    >>> tasks
    [<Task(DagsterPythonOperator): hello_cereal>]


Running a pipeline on Airflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ensure that the Airflow webserver, scheduler (and any workers appropriate to the executor you have
configured) are running. The ``dagster-airflow`` CLI tool will automatically put the generated DAG
definition in ``$AIRLFLOW_HOME/dags``, but if you have a different setup, you should make sure that
this file is wherever the Airflow webserver looks for DAG definitions.

When you fire up the Airflow UI, you should see the new DAG:

.. thumbnail:: intro_airflow_one.png

Kick off a run manually, and you'll be able to use the ordinary views of the pipeline's progress:

.. thumbnail:: intro_airflow_dag_view.png

And logs will be available in the Airflow log viewer:

.. thumbnail:: intro_airflow_logs_view.png

More sophisticated setups
^^^^^^^^^^^^^^^^^^^^^^^^^

This approach requires that Dagster, all of the Python requirements of your Dagster pipelines, and
your Dagaster pipelines themselves be importable in the environment in which your Airflow tasks
operate, because under the hood it uses Airflow's :py:class:`airflow:PythonOperator` to define
tasks.

``dagster-airflow`` also includes facilities for compiling Dagster pipelines to Airflow DAGs whose
tasks use the :py:class:`DockerOperator <airflow:airflow.operators.docker_operator.DockerOperator>` or
:py:class:`KubernetesPodOperator <airflow:airflow.contrib.operators.kubernetes_pod_operator.KubernetesPodOperator>`.
For details, see the :ref:`deployment guide for Airflow <airflow>`.
