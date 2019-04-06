Resources
=========

We've already learned about logging through the info object. We can also use the info object
to manage pipelines' access to resources like the file system, databases, or cloud services.
In general, interactions with features of the external environment like these should be modeled
as resources.

Let's imagine that we are using a key value store offered by a cloud service that has a python API.
We are going to record the results of computations in that key value store.

We are going to model this key value store as a resource.

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/resources.py
   :lines: 1

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/resources.py
   :lines: 28-41, 64-76

The core of a resource are the definition of its configuration (the ``config_field``)
and then the function that can actually construct the resource. Notice that all of the
configuration specified for a given resource is passed to its constructor under the 
``resource_config`` key of the ``init_context`` parameter.

Let's now attach this resource to a pipeline and use it in a solid.

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/resources.py
   :lines: 79-93, 97-101

Resources are attached to pipeline context definitions. A pipeline context
definition is way that a pipeline can declare the different "modes" it can
operate in. For example, a common context definition would be "unittest"
or "production". So, you can swap out implementations of these resources
by altering configuration, while not changing your code.

In this case we have a single context definition, ``cloud``, and that context definition has a 
single resource, the cloud store resource.

In order to invoke this pipeline, we pass it the following configuration:

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/resources.py
   :lines: 105-129
   :dedent: 4

Note how we are telling the configuration to create a cloud context by
using the ``cloud`` key under ``context`` and then parameterizing the store resource
with the appropriate config. As a config, any user-provided configuration for
an artifact (in this case the ``store`` resoource) is placed under the ``config`` key.

So this works, but imagine we wanted to have a test mode, where we interacted
with an in memory version of that key value store and not develop against the live
public cloud version.

First, we need a version of the store that implements the same interface as the production key-value
store; this version can be used in testing contexts without touching the public cloud:

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/resources.py
   :lines: 43-53

Next we package this up as a resource.

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/resources.py
   :lines: 56-62

And lastly add a new context definition to represent this new operating "mode":

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/resources.py
   :lines: 89-101
   :emphasize-lines: 6-8

Now we can simply change configuration and the "in-memory" version of the
resource will be used instead of the cloud version:

.. literalinclude:: ../../../../dagster/tutorials/intro_tutorial/resources.py
   :lines: 131-144
   :emphasize-lines: 4
   :dedent: 4

In the next section, we'll see how to declaratively specify :doc:`Repositories <repos>` to 
manage collections of multiple dagster pipelines.
