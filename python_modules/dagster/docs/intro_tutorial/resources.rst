Resources
=========

We've already learned about execution context logging. Another important capability
of execution context is resources. Pipelines frequently need access to the file system,
databases, or other cloud services. Access to these things should be modelled as resources.

Let's imagine that we are using a key value offered by a cloud service that has a python API.
We are going to record the results of computations in that key value store.

We are going to model this key value store as a "Resource".

.. code-block:: python

    from bigco import PublicCloudConn, set_value_in_cloud_store

    class PublicCloudStore:
        def __init__(self, username, password):
            # create credential and store it
            self.conn = PublicCloudConn(username, password)

        def record_value(self, context, key, value):
            context.info(
                'Setting key={key} value={value} in cloud'.format(
                    key=key, value=value
                )
            )
            set_value_in_cloud_store(self.conn, key, value)

    def define_cloud_store_resource():
        return ResourceDefinition(
            resource_fn=lambda info: PublicCloudStore(
                info.config['username'],
                info.config['password'],
            ),
            config_field=Field(
                Dict({
                    'username': Field(String),
                    'password': Field(String)
                })
            ),
            description='''This represents some cloud-hosted key
            value store. Username and password must be provided
            via configuration for this to work''',
    )

The core of a resource are the definition of its configuration (the `config_field`)
and then the function that can produce the resource.

Let us now attach this to a pipeline and use this resource in a solid.

.. code-block:: python

    @solid(
        inputs=[
            InputDefinition('num_one', Int),
            InputDefinition('num_two', Int)
        ],
        outputs=[OutputDefinition(Int)],
    )
    def add_ints(info, num_one, num_two):
        result = num_one + num_two
        info.context.resources.store.record_value(
            info.context, 'add', result
        )
        return result


    def define_resource_test_pipeline():
        return PipelineDefinition(
            name='resource_test_pipeline',
            solids=[add_ints],
            context_definitions={
                'cloud': PipelineContextDefinition(
                    resources={
                        'store': define_cloud_store_resource()
                    }
                )
            }
        )

Resources are attached to pipeline context definitions. A pipeline context
definition is way that a pipeline can declare the different "modes" it can
operate in. For example a common context definition would be "unittest"
or "production". In a particular context definition you can provide a different
set of resources. That means you can swap out implementations of these resources
by altering configuration, while not changing your code.

In this case we have a single context definition "cloud" and that has a single
resource.

In order to invoke this pipeline, we pass it the following configuration:

.. code-block:: python

    result = execute_pipeline(
        define_resource_test_pipeline(),
        environment={
            'context': {
                'cloud': {
                    'resources': {
                        'store': {
                            'config': {
                                'username': 'some_user',
                                'password': 'some_password',
                            }
                        }
                    }
                }
            },
            'solids': {
                'add_ints': {
                    'inputs': {
                        'num_one': {'value': 2},
                        'num_two': {'value': 6}
                    }
                }
            },
        },
    )

Note how we are telling the configuration to create a cloud context by
using the ``cloud`` key under ``context`` and then parameterizing the store resource
with the appropriate config. As a config, any user-provided configuration for
an artifact (in this case the ``store`` resoource) is placed under the ``config`` key.

So this works, but let us imagine we wanted to have a test mode where we interacted
with an in memory version of that key value store and not develop against the live
public cloud version.

First we need a version of the store that implements the same interface that can be used
in testing contexts but does not touch the public cloud:

.. code-block:: python

    class InMemoryStore:
        def __init__(self):
            self.values = {}

        def record_value(self, context, key, value):
            context.info(
                'Setting key={key} value={value} in memory'.format(
                    key=key, value=value
                )
            )
            self.values[key] = value

Next we package this up as a resource.

.. code-block:: python

    def define_in_memory_store_resource():
        return ResourceDefinition(
            resource_fn=lambda _: InMemoryStore(),
            description='''An in-memory key value store that 
            requires no configuration. Useful for unittesting.''',
        )

And lastly add a new context definition to represent this new operating "mode":

.. code-block:: python

    def define_resource_test_pipeline():
        return PipelineDefinition(
            name='resource_test_pipeline',
            solids=[add_ints],
            context_definitions={
                'cloud': PipelineContextDefinition(
                    resources={
                        'store': define_cloud_store_resource()
                    }
                ),
                'local': PipelineContextDefinition(
                    resources={
                        'store': define_in_memory_store_resource()
                    }
                ),
            }
        )

Now we can simply change configuration and the "in-memory" version of the
resource will be used instead of the cloud version:

.. code-block:: python

    result = execute_pipeline(
        define_resource_test_pipeline(),
        environment={
            'context': {'local': {}},
            'solids': {
                'add_ints': {
                    'inputs': {
                        'num_one': {'value': 2},
                        'num_two': {'value': 6}
                    }
                }
            },
        },

