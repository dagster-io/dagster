Configuration
-------------
So far we have only demonstrated pipelines whose solids yield hardcoded values and then flow them
through the pipeline. In order to be useful a pipeline must also interact with its external
environment.

For maximum flexibility, testability, and reusability, we want to avoid hardcoding solids'
(or pipelines') dependencies on the external world. Configuration is the mechanism dagster
provides to make that possible.

Let's return to our hello world example. But this time, we'll parametrize the string that the
solid yields through config.

This time, we'll use a more fully-featured API to define our solid -- ``@solid`` instead of
``@lambda_solid``.

.. literalinclude:: ../../tutorials/intro_tutorial/part_four.py
   :linenos:
   :caption: part_four.py


You'll notice a new API, ``solid``. We will be exploring this API in much more detail as these
tutorials proceed. For now, the only difference is that the function annotated by solid now
takes one parameter where before it took zero (if it accepted no inputs). This
new parameter is the info parameter, which is of type :py:class:`TransformExecutionInfo`. It
has a property config, which is the configuration that is passed into this
particular solid.

We must provide that configuration. So turn your attention to the second argument
of execute_pipeline, which must be a dictionary. This dictionary 
encompasses *all* of the configuration to execute an entire pipeline, and directly mirrors
the structure of the environment yaml file. It has many
sections. One of these is configuration provided on a per-solid basis, which is what
we are using here. The ``solids`` property is a dictionary keyed by
solid name. These dictionaries take a 'config' property which must correspond to the user-
defined configuration of that particular solid. In this case it takes the value
that will be passed directly to the solid in question, here a string to be printed.

So save this example as step_four.py

.. code-block:: sh

	$ dagster pipeline execute -f part_four.py -n define_pipeline
