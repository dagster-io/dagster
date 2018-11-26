Expectations
============

Dagster has a first-class concept to capture data quality tests. We call these
data quality tests expectations.

Data pipelines have the property that they typically do not control
what data they ingest. Unlike a traditional application where you can
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
        config_field=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def ingest_a(info):
        return info.config


    @solid(
        config_field=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def ingest_b(info):
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
            solids=[ingest_a, ingest_b, add_ints],
            dependencies={
                'add_ints': {
                    'num_one': DependencyDefinition('ingest_a'),
                    'num_two': DependencyDefinition('ingest_b'),
                },
            },
        )

Imagine that we had assumptions baked into the code of this pipeline such that the code only
worked on positive numbers, and we wanted to communicate that requirement to the user
in clear terms. We'll add an expectation in order to do this.


.. code-block:: python

    @solid(
        config_field=ConfigDefinition(types.Int),
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
    def ingest_a(info):
        return info.config


You'll notice that we added an ExpectationDefinition to the output of ingest_a. Expectations
can be attached to inputs or outputs and operate on the value of that input or output.

Expectations perform arbitrary computation on that value and then return an ExpectationResult.
The user communicates whether or not the expectation succeeded via this return value.

If you run this pipeline, you'll notice some logging that indicates that the expectation
was processed:

.. code-block:: python

    execute_pipeline(
        define_part_ten_step_one(), 
        {
            'context': {
                'default': {
                    'config': {
                        'log_level': 'DEBUG',
                    }
                }
            },
            'solids': {
                'ingest_a': {
                    'config': 2,
                },
                'ingest_b': {
                    'config': 3,
                },
            }
        },
    )

And run it...

.. code-block:: sh

    $ python part_ten.py
    ... log spew
    2018-09-14 13:13:13 - dagster - DEBUG - orig_message="Expectation ingest_a.result.expectation.check_positive succeeded on 2." log_message_id="938ab7fa-c955-408a-9f44-66b0b6ecdcad" pipeline="part_ten_step_one" solid="ingest_a" output="result" expectation="check_positive" 
    ... more log spew 

Now let's make this fail. Currently the default behavior is to throw an error and halt execution
when an expectation fails. So:

.. code-block:: python

    execute_pipeline(
        define_part_ten_step_one(), 
        {
            'context': {
                'default': {
                    'config': {
                        'log_level': 'DEBUG',
                    }
                }
            },
            'solids': {
                'ingest_a': {
                    'config': -5,
                },
                'ingest_b': {
                    'config': 3,
                },
            }
        },
    )

And then:

.. code-block:: sh

    $ python part_ten.py
    ... bunch of log spew
    dagster.core.errors.DagsterExpectationFailedError: DagsterExpectationFailedError(solid=add_ints, output=result, expectation=check_positivevalue=-2)

We can also tell execute_pipeline to not throw on error:

.. code-block:: python

    execute_pipeline(
        define_part_ten_step_one(), 
        {
            'context': {
                'default': {
                    'config': {
                        'log_level': 'DEBUG',
                    }
                }
            },
            'solids': {
                'ingest_a': {
                    'config': -5,
                },
                'ingest_b': {
                    'config': 3,
                },
            }
        },
        throw_on_error=False,
    )

.. code-block:: sh

    $ python part_ten.py
    ... log spew
    2018-11-08 10:38:28 - dagster - DEBUG - orig_message="Expectation add_ints.result.expectation.check_positive failed on -2." log_message_id="9ca21f5c-0578-4b3f-80c2-d129552525a4" run_id="c12bdc2d-c008-47db-8b76-e257262eab79" pipeline="part_ten_step_one" solid="add_ints" output="result" expectation="check_positive"

Because the system is explictly aware of these expectations they are viewable in tools like dagit.
It can also configure the execution of these expectations. The capabilities of this aspect of the
system are currently quite immature, but we expect to develop these more in the future. The only
feature right now is the ability to skip expectations entirely. This is useful in a case where
expectations are expensive and you have a time-critical job you must. In that case you can
configure the pipeline to skip expectations entirely.


.. code-block:: python

    execute_pipeline(
        define_part_ten_step_one(), 
        {
            'context': {
                'default': {
                    'config': {
                        'log_level': 'DEBUG',
                    }
                }
            },
            'solids': {
                'ingest_a': {
                    'config': 2,
                },
                'ingest_b': {
                    'config': 3,
                },
            },
            'expectations': {
                'evaluate': False,
            },
        },
    )

.. code-block:: sh

    $ python part_ten.py
    ... expectations will not in the log spew 

We plan on adding more sophisticated capabilties to this in the future.
