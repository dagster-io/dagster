Parametrizing pipelines with resources
--------------------------------------

Often, we'll want to be able to configure pipeline-wide facilities, like uniform access to the
file system, databases, or cloud services. Dagster models interactions with features of the external
environment like these as resources (and library modules such as ``dagster_aws``, ``dagster_gcp``,
and even ``dagster_slack`` provide out-of-the-box implementations for many common external
services).

Typically, your data processing pipelines will want to store their results in a data warehouse
somewhere separate from the raw data sources. We'll adjust our toy pipeline so that it does a little
more work on our cereal dataset, stores the finished product in a swappable data warehouse, and
lets the team know when we're finished.

You might have noticed that our cereal dataset isn't normalized -- that is, the serving sizes for
some cereals are as small as a quarter of a cup, and for others are as large as a cup and a half.
This grossly understates the nutritional difference between our different cereals.

Let's transform our dataset and then store it in a normalized table in the warehouse:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/resources.py
    :caption: resources.py
    :linenos:
    :lineno-start: 57
    :lines: 57-80
    :emphasize-lines: 24

Resources are another facility that Dagster makes available on the ``context`` object passed to
solid logic. Note that we've completely encapsulated access to the database behind the call to
``context.resources.warehouse.update_normalized_cereals``. This means that we can easily swap resource
implementations -- for instance, to test against a local SQLite database instead of a production
Snowflake database; to abstract software changes, such as swapping raw SQL for SQLAlchemy; or to
accomodate changes in business logic, like moving from an overwriting scheme to append-only,
date-partitioned tables.

To implement a resource and specify its config schema, we use the
:py:class:`@resource <dagster.resource>` decorator. The decorated function should return whatever
object you wish to make available under the specific resource's slot in ``context.resources``.
Resource constructor functions have access to their own ``context`` argument, which gives access to
resource-specific config. (Unlike the contexts we've seen so far, which are instances of
:py:class:`SystemComputeExecutionContext <dagster.SystemComputeExecutionContext>`, this context is
an instance of :py:class:`InitResourceContext <dagster.InitResourceContext>`.)

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/resources.py
    :caption: resources.py
    :linenos:
    :lineno-start: 16
    :lines: 16-45
    :emphasize-lines: 28-30

The last thing we need to do is to attach the resource to our pipeline, so that it's properly
initialized when the pipeline run begins and made available to our solid logic as
``context.resources.warehouse``.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/resources.py
    :caption: resources.py
    :linenos:
    :lineno-start: 83
    :lines: 83-91
    :emphasize-lines: 2-6

All resources are associated with a :py:class:`ModeDefinition <dagster.ModeDefinition>`. So far,
all of our pipelines have had only a single, system default mode, so we haven't had to tell Dagster
what mode to run them in. Even in this case, where we provide a single anonymous mode to the
:py:func:`@pipeline <dagster.pipeline>` decorator, we won't have to specify which mode to use (it
will take the place of the ``default`` mode).

We can put it all together with the following config:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/resources.yaml
    :caption: resources.yaml
    :language: YAML
    :linenos:
    :emphasize-lines: 1-4

(Here, we pass the special string ``":memory:"`` in config as the connection string for our
database -- this is how SQLite designates an in-memory database.)


Expressing resource dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We've provided a ``warehouse`` resource to our pipeline, but we're still manually managing our
pipeline's dependency on this resource. Dagster also provides a way for solids to advertise
their resource requirements, to make it easier to keep track of which resources need to be
provided for a pipeline.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/required_resources.py
    :caption: required_resources.py
    :linenos:
    :lineno-start: 55
    :lines: 55-78
    :emphasize-lines: 1

Now, the Dagster machinery knows that this solid requires a resource called ``warehouse`` to be
present on its mode definitions, and will complain if that resource is not present.


Pipeline modes
--------------

By attaching different sets of resources with the same APIs to different modes, we can support
running pipelines -- with unchanged business logic -- in different environments. So you might have
a "unittest" mode that runs against an in-memory SQLite database, a "dev" mode that runs against
Postgres, and a "prod" mode that runs against Snowflake.

Separating the resource definition from the business logic makes pipelines testable. As long as the
APIs of the resources agree, and the fundamental operations they expose are tested in each
environment, we can test business logic independent of environments that may be very costly or
difficult to test against.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/modes.py
   :lines: 74-83
   :linenos:
   :lineno-start: 74
   :caption: modes.py

Even if you're not familiar with SQLAlchemy, it's enough to note that this is a very different
implementation of the ``warehouse`` resource. To make this implementation available to Dagster, we
attach it to a :py:class:`ModeDefinition <dagster.ModeDefinition>`.

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/modes.py
   :lines: 126-141
   :linenos:
   :lineno-start: 126
   :caption: modes.py

Each of the ways we can invoke a Dagster pipeline lets us select which mode we'd like to run it in.

From the command line, we can set ``-d`` or ``--mode`` and select the name of the mode:

.. code-block:: shell

    $ dagster pipeline execute -f modes.py -n modes_pipeline -d dev

From the Python API, we can use the :py:class:`RunConfig <dagster.RunConfig>`:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/modes.py
   :lines: 151-155
   :linenos:
   :lineno-start: 151
   :emphasize-lines: 4
   :dedent: 4
   :caption: modes.py

And in Dagit, we can use the "Mode" selector to pick the mode in which we'd like to execute.

.. thumbnail:: modes.png

The config editor is Dagit is mode-aware, so when you switch modes and introduce a resource that
requires additional config, the editor will prompt you.

Pipeline config presets
-----------------------

Useful as the Dagit config editor and the ability to stitch together YAML fragments is, once
pipelines have been productionized and config is unlikely to change, it's often useful to distribute
pipelines with embedded config. For example, you might point solids at different S3 buckets in
different environments, or want to pull database credentials from different environment variables.

Dagster calls this a config preset:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/presets.py
   :lines: 127-166
   :linenos:
   :lineno-start: 127
   :caption: presets.py
   :emphasize-lines: 14-37

We illustrate two ways of defining a preset.

The first is to pass an ``environment_dict`` literal to the constructor. Because this dict is
defined in Python, you can do arbitrary computation to construct it -- for instance, picking up
environment variables, making a call to a secrets store like Hashicorp Vault, etc.

The second is to use the ``from_files`` static constructor, and pass a list of file globs from 
which to read YAML fragments. Order matters in this case, and keys from later files will overwrite
keys from earlier files.

To select a preset for execution, we can use the CLI, the Python API, or Dagit.

From the CLI, use ``-p`` or ``--preset``:

.. code-block:: shell

    $ dagster pipeline execute -f modes.py -n modes_pipeline -p unittest

From Python, you can use :py:func:`execute_pipeline_with_preset <dagster.execute_pipeline_with_preset>`:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/presets.py
   :lines: 169
   :dedent: 4

And in Dagit, we can use the "Presets" selector. 

.. thumbnail:: presets.png
