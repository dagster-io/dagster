Expectations
============

Dagster has a first-class concept to capture data quality tests. We call these
data quality tests expectations.

Data pipelines have the property that they typically do not control
what data they injest. Unlike a traditional application where you can
prevent users from entering malformed data, data pipelines do not have
that option. When unexpected data enters a pipeline and causes a software
error, typically the only recourse is to update your code. 

Lying within the code of data pipelines are a whole host of implicit
assumptions about the nature of the data. One way to frame the goal of
expectations is to say that they make those implict assumption explicit.
And by making these a first class concept they can be described with metadata,
inspected, and configured to run in different ways.

Let us return to a slightly simplified version of the data pipeline from part nine.

.. code-block:: python

    @solid(
        config_def=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def injest_a(info):
        return info.config


    @solid(
        config_def=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def injest_b(info):
        return info.config

    @solid(
        inputs=[InputDefinition('num_one', types.Int),
                InputDefinition('num_two', types.Int)],
        outputs=[OutputDefinition(types.Int)],
    )
    def add_ints(_info, num_one, num_two):
        return num_one + num_two


    def define_part_ten_step_one():
        return PipelineDefinition(
            name='part_ten_step_one',
            solids=[injest_a, injest_b, add_ints],
            dependencies={
                'add_ints': {
                    'num_one': DependencyDefinition('injest_a'),
                    'num_two': DependencyDefinition('injest_b'),
                },
            },
        )

Imagine that we had assumptions baked into the code of this pipeline such that the code only
worked on positive numbers, and we wanted to communicate that requirement to the user
in clear terms. We'll add an expectation in order to do this.


.. code-block:: python

    @solid(
        config_def=ConfigDefinition(types.Int),
        outputs=[
            OutputDefinition(
                types.Int,
                expectations=[
                    ExpectationDefinition(
                        name="check_positive",
                        expectation_fn=lambda _info, value: ExpectationResult(success=value > 0)
                    ),
                ],
            ),
        ],
    )
    def injest_a(info):
        return info.config


You'll notice that we added an ExpectationDefinition to the output of injest_a. Expectations
can be attached to inputs or outputs and operate on the value of that input or output.

Expectations perform arbitrary computation on that value and then return an ExpectationResult.
The user communicates whether or not the expectation succeeded via this return value.

If you run this pipeline, you'll notice some logging that indicates that the expectation
was processed:

.. code-block:: python

    execute_pipeline(
        define_part_ten_step_one(), 
        config.Environment(
            context=config.Context(config={
                'log_level': 'DEBUG',
            }),
            solids={
                'injest_a': config.Solid(2),
                'injest_b': config.Solid(3),
            }
        ),
    )

And run it...

.. code-block:: sh

    $ python part_ten.py
    ... log spew
    2018-09-14 13:13:13 - dagster - DEBUG - orig_message="Expectation injest_a.result.expectation.check_positive succeeded on 2." log_message_id="938ab7fa-c955-408a-9f44-66b0b6ecdcad" pipeline="part_ten_step_one" solid="injest_a" output="result" expectation="check_positive" 
    ... more log spew 

Now let's make this fail. Currently the default behavior is to throw an error and halt execution
when an expectation fails. So:

.. code-block:: python

    execute_pipeline(
        define_part_ten_step_one(), 
        config.Environment(
            context=config.Context(config={
                'log_level': 'DEBUG',
            }),
            solids={
                'injest_a': config.Solid(-2), # oh noes!
                'injest_b': config.Solid(3),
            }
        ),
    )

And then:

.. code-block:: sh

    $ python part_ten.py
    ... bunch of log spew
    dagster.core.errors.DagsterExpectationFailedError: DagsterExpectationFailedError(solid=injest_a, output=result, expectation=check_positivevalue=-2)

We can also tell execute_pipeline to not throw on error:

.. code-block:: python

    execute_pipeline(
        define_part_ten_step_one(), 
        config.Environment(
            context=config.Context(config={
                'log_level': 'DEBUG',
            }),
            solids={
                'injest_a': config.Solid(-2), # oh noes!
                'injest_b': config.Solid(3),
            }
        ),
        throw_on_error=False,
    )

.. code-block:: sh

    $ python part_ten.py
    ... log spew
    2018-09-14 13:31:09 - dagster - DEBUG - orig_message="Expectation injest_a.result.expectation.check_positive failed on -2." log_message_id="24bbaa2a-34a2-4817-b364-199a6d9f6066" pipeline="part_ten_step_one" solid="injest_a" output="result" expectation="check_positive"

Because the system is explictly aware of these expectations they are viewable in tools like dagit.
It can also configure the execution of these expectations. The capabilities of this aspect of the
system are currently quite immature, but we expect to develop these more in the future. The only
feature right now is the ability to skip expectations entirely. This is useful in a case where
expectations are expensive and you have a time-critical job you must. In that case you can
configure the pipeline to skip expectations entirely.


.. code-block:: python

    execute_pipeline(
        define_part_ten_step_one(), 
        config.Environment(
            context=config.Context(config={
                'log_level': 'DEBUG',
            }),
            solids={
                'injest_a': config.Solid(-2), # oh noes!
                'injest_b': config.Solid(3),
            },
            expectations=config.Expectations(evaluate=True),
        ),
    )

.. code-block:: sh

    $ python part_ten.py
    ... expectations will not in the log spew 

We plan on adding more sophisticated capabilties to this in the future.
