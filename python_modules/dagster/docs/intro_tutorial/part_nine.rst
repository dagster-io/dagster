Custom Contexts
---------------

So far we have used contexts for configuring logging level only. This barely scratched the surface
of its capabilities.

Testing data pipelines, for a number of reasons, is notoriously difficult. One of the reasons is
that as one moves a data pipeline from local development, to unit testing, to integration testing, to CI/CD,
to production, or to whatever environment you need to operate in, the operating environment can
change dramatically.

In order to handle this, whenever the business logic of a pipeline is interacting with external resources
or dealing with pipeline-wide state generally, the dagster user is expected to interact with these resources
and that state via the context object. Examples would include database connections, connections to cloud services,
interactions with scratch directories on your local filesystem, and so on.

Let's imagine a scenario where we want to record some custom state in a key-value store for our execution runs.
A production time, this key-value store is a live store (e.g. DynamoDB in amazon) but we do not want to interact
this store for unit-testing. Contexts will be our tool to accomplish this goal.

We're going to have a simple pipeline that does some rudimentary arithmetic, but that wants record
the result computations in that key value store.

Let's first set up a simple pipeline. We injest two numbers (each in their own trivial solid)
and then two downstream solids add and multiple those numbers, respectively.

.. code-block:: python

    @solid(
        config_def=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def injest_a(context, conf):
        return conf


    @solid(
        config_def=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def injest_b(context, conf):
        return conf

    @solid(
        inputs=[InputDefinition('num_one', types.Int),
                InputDefinition('num_two', types.Int)],
        outputs=[OutputDefinition(types.Int)],
    )
    def add_ints(_context, _conf, num_one, num_two):
        return num_one + num_two


    @solid(
        inputs=[InputDefinition('num_one', types.Int),
                InputDefinition('num_two', types.Int)],
        outputs=[OutputDefinition(types.Int)],
    )
    def mult_ints(_context, _conf, num_one, num_two):
        return num_one * num_two
        

    def define_part_nine_step_one():
        return PipelineDefinition(
            name='part_nine',
            solids=[injest_a, injest_b, add_ints, mult_ints],
            dependencies={
                'add_ints': {
                    'num_one': DependencyDefinition('injest_a'),
                    'num_two': DependencyDefinition('injest_b'),
                },
                'mult_ints': {
                    'num_one': DependencyDefinition('injest_a'),
                    'num_two': DependencyDefinition('injest_b'),
                },
            },
        )

Now we configure execution using a env.yml file:

.. code-block:: yaml

    context:
        config: 
        log_level: DEBUG

    solids:
        injest_a:
            config: 2
        injest_b: 
            config: 3

And you should see some log spew indicating execution.

Now imagine we want to log some of the values passing through these solids
into some sort of key value store in cloud storage:

Let's say we have a module called ``cloud`` that allows for interaction
with this key value store. You have to create an instance of a ``PublicCloudConn``
class and then pass that to a function ``set_value_in_cloud_store`` to interact
with the service.

.. code-block:: python

    from cloud import (PublicCloudConn, set_value_in_cloud_store)

    # imagine implementations such as the following
    # class PublicCloudConn:
    #     def __init__(self, creds):
    #         self.creds = creds


    # def set_value_in_cloud_store(_conn, _key, _value):
    #     # imagine this doing something
    #     pass

    conn = PublicCloudConn({'user': some_user', 'pass' : 'some_pwd'})
    set_value_in_cloud_store(conn, 'some_key', 'some_value')


Naively let's add this to one of our transforms:

.. code-block:: python

    @solid(
        config_def=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def injest_a(_context, conf):
        conn = PublicCloudConn('some_user', 'some_pwd')
        set_value_in_cloud_store(conn, 'a', conf)
        return conf

As coded above this is a bad idea on any number of dimensions. One the username/password
combo is hard coded. We could pass it in as a configuration of the solid. However that
is only in scope for that particular solid. So now the configuration would be passed into
each and every solid that needs it. This sucks. The connection would have to be created within
every solid. Either you would have to implement your own connection pooling or take the hit
of a new connection per solid. This also sucks.

More subtley, what was previously a nice, isolated, testable piece of software is now hard-coded
to interact with some externalized resource and requires an internet connection, access to
a cloud service, and that could intermittently fail, and that would be slow relative to pure
in-memory compute. This code is no longer testable in any sort of reliable way.

This is where the concept of the context shines. What we want to do is attach an object to the
context object -- which a single instance of is flowed through the entire execution --  that
provides an interface to that cloud store that caches that connection and also provides a
swappable implementation of that store for test isolation. We want code that ends up looking like
this:

.. code-block:: python

    @solid(
        config_def=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def injest_a(context, conf):
        # The store should be an interface to the cloud store 
        # We will explain the ``resources`` property later.
        context.resources.store.record_value(context, 'a', conf)
        return conf

The user will be able have complete control the creation of the ``store`` object attached to
the ``resources`` object, which allows a pipeline designer to insert seams of testability.

This ends up accomplishing our goal of being able to test this pipeline in multiple environments
with *zero changes to the core business logic.* The only thing that will vary between environments
is configuration and the context generated because of that configuration.

We need this store object, and two implementations of it. One that talks to the public cloud
service, and one that is an in-memory implementation of this.

.. code-block:: python

    class PublicCloudStore:
        def __init__(self, credentials):
            self.conn = PublicCloudConn(credentials)

        def record_value(self, context, key, value):
            context.info('Setting key={key} value={value} in cloud'
                .format(
                    key=key,
                    value=value,
                )
            )
            set_value_in_cloud_store(self.conn, key, value)


    class InMemoryStore:
        def __init__(self):
            self.values = {}

        def record_value(self, context, key, value):
            context.info('Setting key={key} value={value} in memory'.
                format(
                    key=key,
                    value=value,
                )
            )
            self.values[key] = value


Now we need to create one of these stores and put them into the context. The pipeline author must
create a :py:class:`PipelineContextDefinition`.

It two primrary attributes:

1) A configuration definition that allows the pipeline author to define what configuration
is needed to create the ExecutionContext.
2) A function that returns an instance of an ExecutionContext. This context is flowed through
the entire execution.

First let's create the context suitable for local testing:

..code-block:: python

    PartNineResources = namedtuple('PartNineResources', 'store')

    PipelineContextDefinition(
        context_fn=lambda _pipeline_def, _conf: 
            ExecutionContext.console_logging(
                log_level=DEBUG,
                resources=PartNineResources(InMemoryStore())
            )
    )

This context requires *no* configuration so it is not specified. We then 
provide a lambda which creates an ExecutionContext. You'll notice that we pass
in a log_level and a "resources" object. The resources object can be any
python object. What is demonstrated above is a convention. The resources
object that the user creates will be passed through the execution.

So if we return to the implementation of the solids that includes the interaction
with the key-value store, you can see how this will invoke the in-memory store object
which is attached the resources property of the context.

.. code-block:: python

    @solid(
        config_def=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def injest_a(context, conf):
        context.resources.store.record_value(context, 'a', conf)
        return conf

    @solid(
        config_def=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def injest_b(context, conf):
        context.resources.store.record_value(context, 'b', conf)
        return conf


    @solid(
        inputs=[InputDefinition('num_one', types.Int),
                InputDefinition('num_two', types.Int)],
        outputs=[OutputDefinition(types.Int)],
    )
    def add_ints(context, _conf, num_one, num_two):
        result = num_one + num_two
        context.resources.store.record_value(context, 'add', result)
        return result


    @solid(
        inputs=[InputDefinition('num_one', types.Int),
                InputDefinition('num_two', types.Int)],
        outputs=[OutputDefinition(types.Int)],
    )
    def mult_ints(context, _conf, num_one, num_two):
        result = num_one * num_two
        context.resources.store.record_value(context, 'mult', result)
        return result

Now we need to declare the pipeline to use this PipelineContextDefinition. 
We do so with the following:

.. code-block:: python

    return PipelineDefinition(
        name='part_nine',
        solids=[injest_a, injest_b, add_ints, mult_ints],
        dependencies={
            'add_ints': {
                'num_one': DependencyDefinition('injest_a'),
                'num_two': DependencyDefinition('injest_b'),
            },
            'mult_ints': {
                'num_one': DependencyDefinition('injest_a'),
                'num_two': DependencyDefinition('injest_b'),
            },
        },
        context_definitions={
            'local': PipelineContextDefinition(
                context_fn=lambda _pipeline_def, _conf: 
                    ExecutionContext.console_logging(
                        log_level=DEBUG,
                        resources=PartNineResources(InMemoryStore())
                    ),
                )
            ),
        }
    )

You'll notice that we have "named" the context local. Now when we invoke that context,
we config it with that name.

.. code-block:: yaml

    context:
        name: local

    solids:
        injest_a:
            config: 2
        injest_b:
            config: 3

Now run the pipeline and you should see logging indicating the execution is occuring.

Now let us add a different context definition that substitutes in the production
version of that store.

.. code-block:: python

    PipelineDefinition(
        name='part_nine',
        solids=[injest_a, injest_b, add_ints, mult_ints],
        dependencies={
            'add_ints': {
                'num_one': DependencyDefinition('injest_a'),
                'num_two': DependencyDefinition('injest_b'),
            },
            'mult_ints': {
                'num_one': DependencyDefinition('injest_a'),
                'num_two': DependencyDefinition('injest_b'),
            },
        },
        context_definitions={
            'local': PipelineContextDefinition(
                context_fn=lambda _pipeline_def, _conf: 
                    ExecutionContext.console_logging(
                        log_level=DEBUG,
                        resources=PartNineResources(InMemoryStore())
                    )
            ),
            'cloud': PipelineContextDefinition(
                context_fn=lambda _pipeline_def, conf: 
                    ExecutionContext.console_logging(
                        resources=PartNineResources(
                            PublicCloudStore(conf['credentials'],
                        )
                    )
                ),
                config_def=ConfigDefinition(
                    config_type=types.ConfigDictionary({
                        'credentials': Field(types.ConfigDictionary({
                            'user' : Field(types.String),
                            'pass' : Field(types.String),
                        })),
                    }),
                ),
            )
        }
    )

Notice the *second* context definition. It

1) Accepts configuration, the specifies that in a typed fashion.
2) Creates a different version of that store, to which it passes configuration.

Now when you invoke this pipeline with the following yaml file:

.. code-block:: yaml

    context:
        name: cloud
        config:
            credentials:
                user: some_user
                pass: some_password

    solids:
        injest_a:
            config: 2
        injest_b:
            config: 3

It will create the production version of that store. Note that you have
not change the implementation of any solid to do this. Only the configuration
changes.
