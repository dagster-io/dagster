Configuration
-------------

So far we have only demonstrated pipelines that produce hardcoded values
and then flow them through the pipeline. In order to be useful a pipeline
must also interact with its external environment, and in general, it should
use configuration to do so.

For maximum flexiblity, testabilty, and reusability pipelines should be fully
parameterizable. Configuration is how we achieve that end in dagster.

We return to our hello world example, but now we will be able to parameterize
the string printed via config.
 
In order to accomplish this we need to change APIs, from ``lambda_solid`` to ``solid``.
A ``lambda_solid`` only exposes a subset of solid features in order to provide a more
minimal API. ``solid`` is more complicated, and has more capabilities:

.. code-block:: python

    from dagster import (
        ConfigDefinition,
        PipelineDefinition,
        execute_pipeline,
        solid,
        types,
    )

    @solid(config_def=ConfigDefinition(types.String))
    def hello_world(info):
        print(info.config)

    def define_pipeline():
        return PipelineDefinition(solids=[hello_world])


    if __name__ == '__main__':
        execute_pipeline(
            define_pipeline(),
            {
                'solids': {
                    'hello_world': {
                        'config': 'Hello, World!',
                    },
                },
            },
        )

You'll notice a new API, ``solid``. We will be exploring this API in much more detail as these
tutorials proceed. For now, the only difference is that the function annotated by solid now
takes one parameter where before it took zero (if it accepted no inputs). This
new paramater is the info parameter, which is of type :py:class:`TransformExecutionInfo`. It
has a property config, which is the configuration that is passed into this
particular solid.

We must provide that configuration. And thusly turn your attention to the second argument
of execute_pipeline, which must be a dictinoary. This dictinoary 
encompasses *all* of the configuration to execute an entire pipeline, and directly mirrors
the structure of the environment yaml file. It has many
sections. One of these is configuration provided on a per-solid basis, which is what
we are using here. The ``solids`` property is a dictionary keyed by
solid name. These dictionaries take a 'config' property which must correspond to the user-
defined configuration of that particular solid. In this case it takes the value
that will be passed directly to the solid in question, in this case a string to be printed.

So save this example as step_four.py

.. code-block:: sh

	$ dagster pipeline execute -f part_four.py -n define_pipeline
