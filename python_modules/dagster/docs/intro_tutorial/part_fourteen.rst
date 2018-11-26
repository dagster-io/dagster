Unit-testing Pipelines
----------------------

Unit testing data pipelines is, broadly speaking, quite difficult. As a result, it is typically
never done.

One of the mechanisms included in dagster to enable testing has already been discussed: contexts.
The other mechanism is the ability to execute arbitrary subsets of a DAG. (This capability is
useful for other use cases but we will focus on unit testing for now).

Let us start where we left off.

We have the following pipeline:

.. code-block:: python

    @solid(
        config_field=ConfigDefinition(types.Int),
        outputs=[OutputDefinition(types.Int)],
    )
    def load_number(info):
        return info.config


    @lambda_solid(
        inputs=[
            InputDefinition('num1', types.Int),
            InputDefinition('num2', types.Int),
        ],
        output=OutputDefinition(types.Int),
    )
    def adder(num1, num2):
        return num1 + num2


    @lambda_solid(
        inputs=[
            InputDefinition('num1', types.Int),
            InputDefinition('num2', types.Int),
        ],
        output=OutputDefinition(types.Int),
    )
    def multer(num1, num2):
        return num1 * num2


    def define_part_fourteen_step_one():
        # (a + b) * (c + d)

        return PipelineDefinition(
            name='tutorial_part_thirteen_step_one',
            solids=[load_number, adder, multer],
            dependencies={
                SolidInstance(load_number.name, 'a'): {},
                SolidInstance(load_number.name, 'b'): {},
                SolidInstance(load_number.name, 'c'): {},
                SolidInstance(load_number.name, 'd'): {},
                SolidInstance(adder.name, 'a_plus_b'): {
                    'num1': DependencyDefinition('a'),
                    'num2': DependencyDefinition('b'),
                },
                SolidInstance(adder.name, 'c_plus_d'): {
                    'num1': DependencyDefinition('c'),
                    'num2': DependencyDefinition('d'),
                },
                SolidInstance(multer.name, 'final'): {
                    'num1': DependencyDefinition('a_plus_b'),
                    'num2': DependencyDefinition('c_plus_d'),
                },
            },
        )

Let's say we wanted to test *one* of these solids in isolation.

We want to do is isolate that solid and execute with inputs we
provide, instead of from solids upstream in the dependency graph.

So let's do that. Follow along in the comments:

.. code-block:: python

    # The pipeline returned is a new unnamed, pipeline
    # that contains the isolated solid plus the injected solids
    # that will satisfy it inputs
    pipeline = PipelineDefinition.create_single_solid_pipeline(
        #
        # This takes an existing pipeline
        #
        define_part_fourteen_step_one(),
        #
        # Isolates a single solid. In this case "final"
        #
        'final',
        #
        # Final has two inputs, num1 and num2. You must provide
        # values for this. So we create solids in memory to provide
        # values. The solids we are just emit the passed in values
        # as an output
        #
        injected_solids={
            'final': {
                'num1': define_stub_solid('stub_a', 3),
                'num2': define_stub_solid('stub_b', 4),
            }
        }
    )

    result = execute_pipeline(pipeline)

    assert result.success
    assert len(result.result_list) == 3
    assert result.result_for_solid('stub_a').transformed_value() == 3
    assert result.result_for_solid('stub_b').transformed_value() == 4
    assert result.result_for_solid('final').transformed_value() == 12

We can also execute entire arbitrary subdags rather than a single solid.


.. code-block:: python

    def test_a_plus_b_final_subdag():
        pipeline = PipelineDefinition.create_sub_pipeline(
            define_part_fourteen_step_one(),
            ['a_plus_b', 'final'],
            ['final'],
            injected_solids={
                'a_plus_b': {
                    'num1': define_stub_solid('stub_a', 2),
                    'num2': define_stub_solid('stub_b', 4),
                },
                'final': {
                    'num2': define_stub_solid('stub_c_plus_d', 6),
                }
            },
        )

        pipeline_result = execute_pipeline(pipeline)

        assert pipeline_result.result_for_solid('a_plus_b').transformed_value() == 6
        assert pipeline_result.result_for_solid('final').transformed_value() == 36
