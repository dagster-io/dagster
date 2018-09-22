Reusable Solids
---------------

So far we have been using solids tailor-made for each pipeline they were resident in, and have
only used a single instance of that solid. However, solids are, at their core, a specialized type
of function. And like functions, they should be reusable and not tied to a particular call site.

Now imagine we a pipeline like the following:

.. code-block:: python

    @solid(config_def=ConfigDefinition(types.Int), outputs=[OutputDefinition(types.Int)])
    def load_a(info):
        return info.config


    @solid(config_def=ConfigDefinition(types.Int), outputs=[OutputDefinition(types.Int)])
    def load_b(info):
        return info.config


    @lambda_solid(
        inputs=[
            InputDefinition('a', types.Int),
            InputDefinition('b', types.Int),
        ],
        output=OutputDefinition(types.Int),
    )
    def a_plus_b(a, b):
        return a + b


    def define_part_thirteen_step_one():
        return PipelineDefinition(
            name='thirteen_step_one',
            solids=[load_a, load_b, a_plus_b],
            dependencies={
                'a_plus_b': {
                    'a': DependencyDefinition('load_a'),
                    'b': DependencyDefinition('load_b'),
                }
            }
        )


    def test_part_thirteen_step_one():
        pipeline_result = execute_pipeline(
            define_part_thirteen_step_one(),
            config.Environment(solids={
                'load_a': config.Solid(234),
                'load_b': config.Solid(384),
            })
        )

        assert pipeline_result.success
        solid_result = pipeline_result.result_for_solid('a_plus_b')
        assert solid_result.transformed_value() == 234 + 384


You'll notice that the solids in this pipeline are very generic. There's no reason why we shouldn't be able
to reuse them. Indeed load_a and load_b only different by name. What we can do is include multiple
instances of a particular solid in the dependency graph, and alias them. We can make the three specialized
solids in this pipeline two generic solids, and then hook up three instances of them in a dependency
graph:

.. code-block:: python

    @solid(
        config_def=ConfigDefinition(types.Int),
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


    def define_part_thirteen_step_two():
        return PipelineDefinition(
            name='thirteen_step_two',
            solids=[load_number, adder],
            dependencies={
                SolidInstance('load_number', alias='load_a'): {},
                SolidInstance('load_number', alias='load_b'): {},
                SolidInstance('adder', alias='a_plus_b'): {
                    'num1': DependencyDefinition('load_a'),
                    'num2': DependencyDefinition('load_b'),
                }
            }
        )


    def test_part_thirteen_step_two():
        pipeline_result = execute_pipeline(
            define_part_thirteen_step_two(),
            config.Environment(solids={
                'load_a': config.Solid(23),
                'load_b': config.Solid(38),
            })
        )

        assert pipeline_result.success
        solid_result = pipeline_result.result_for_solid('a_plus_b')
        assert solid_result.transformed_value() == 23 + 38


You can think of the solids parameter as declaring what solids are "in-scope" for the
purposes of this pipeline, and the dependencies parameter is how they instantiated
and connected together. Within the dependency graph and in config, the alias of the
particular instance is used, rather than the name of the definition.

Load this in dagit and you'll see that the node are the graph are labeled with
their instance name.

.. code-block:: sh

        $ dagit -f part_thirteen.py -n define_part_thirteen_step_two 

These can obviously get more complicated and involved, with solids being reused
many times:

.. code-block:: python

    def define_part_thirteen_step_three():
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

Now these arithmetic operations are not particularly interesting, but one
can imagine reusable solids doing more useful things like uploading files
to cloud storage, unzipping files, etc.
