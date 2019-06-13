Resources
=========

We've already learned about logging through the context object. We can also use the context object
to manage pipelines' access to resources like the file system, databases, or cloud services. In
general, interactions with features of the external environment like these should be modeled as
resources, and dagster provides out-of-the-box support for many integrations_ with data-oriented AWS
products like S3 and EMR, and similar for GCP products like Cloud Dataproc and BigQuery.

Here, we're going to walk through an example of using the Slack resource to post a message to Slack.

You'll first need to ``pip install dagster_slack`` to get the integration—see the Slack_ integration
getting started guide to get set up. Let's attach the Slack resource to a pipeline and use it in a
solid. Put the following into a file ``resources.py``:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/resources_one.py
    :caption: resources.py
    :linenos:
    :lines: 3-17,22-31

Provide your Slack token, and choose a channel and message. Then running this with ``python
resources.py``, you should see a message from ``dagsterbot`` appear in your Slack channel.

.. _integrations: https://github.com/dagster-io/dagster#integrations
.. _Slack: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-slack


Modes
=====
Resources are attached to a set of :py:class:`ModeDefinition <dagster.ModeDefinition>` defined on
the pipeline. A :py:class:`ModeDefinition <dagster.ModeDefinition>` is the way that a pipeline can
declare the different "modes" it can operate in. For example, you may have "unittest", "local", or
"production" modes that allow you to swap out implementations of resources by altering
configuration, while not changing your code.

Let's say that when running locally, you don't want your pipeline to generate noise in your Slack
instance, and instead are happy to save the Slack messages to a local file. We'll first implement
a simple resource that provides the same ``.chat.post_message()`` API, using the ``@resource``
decorator:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/resources_full.py
   :lines: 25-41
   :linenos:
   :emphasize-lines: 3,10

As you can see, this resource has a different configuration. As highlighted above, instead of
requiring a Slack token, we've specified an "output_path" string configuration for the name of the file
it'll write to.

In order to run this pipeline, we invoke it in this way:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/resources_full.py
   :lines: 67-73
   :linenos:
   :dedent: 4
   :emphasize-lines: 4-6

Now we can simply change the mode via :py:class:`RunConfig <dagster.RunConfig>` to toggle which
implementation of ``slack`` is used. The complete example including both "local" and "production"
modes is shown below:

.. literalinclude:: ../../../../examples/dagster_examples/intro_tutorial/resources_full.py
    :emphasize-lines: 61-64, 69-72 
    :linenos:
    :caption: resources_full.py

Note for each of the ``execute_pipeline`` invocations we are selecting a mode via the
:py:class:`RunConfig <dagster.RunConfig>` and then parameterizing the ``slack`` resource with the
appropriate config for that mode.

In the next section, we'll see how to declaratively specify :doc:`Repositories <repos>` to
manage collections of multiple dagster pipelines.
