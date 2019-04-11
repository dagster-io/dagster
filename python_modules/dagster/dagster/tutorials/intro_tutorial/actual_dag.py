from dagster import DependencyDefinition, InputDefinition, PipelineDefinition, lambda_solid


@lambda_solid
def solid_a():
    return 1


@lambda_solid(inputs=[InputDefinition('arg_a')])
def solid_b(arg_a):
    return arg_a * 2


@lambda_solid(inputs=[InputDefinition('arg_a')])
def solid_c(arg_a):
    return arg_a * 3


@lambda_solid(inputs=[InputDefinition('arg_b'), InputDefinition('arg_c')])
def solid_d(arg_b, arg_c):
    return arg_b * arg_c


def define_diamond_dag_pipeline():
    return PipelineDefinition(
        name='actual_dag_pipeline',
        # The order of this list does not matter:
        # dependencies determine execution order
        solids=[solid_d, solid_c, solid_b, solid_a],
        dependencies={
            'solid_b': {'arg_a': DependencyDefinition('solid_a')},
            'solid_c': {'arg_a': DependencyDefinition('solid_a')},
            'solid_d': {
                'arg_b': DependencyDefinition('solid_b'),
                'arg_c': DependencyDefinition('solid_c'),
            },
        },
    )
