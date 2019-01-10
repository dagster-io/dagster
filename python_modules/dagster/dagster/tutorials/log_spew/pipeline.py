import time

from dagster import (
    DependencyDefinition,
    InputDefinition,
    MultipleResults,
    OutputDefinition,
    PipelineDefinition,
    solid,
    SolidInstance,
)


def nonce_solid(name, n_inputs, n_outputs):
    """Creates a solid with the given number of (meaningless) inputs and outputs.

    Config controls the behavior of the nonce solid."""

    @solid(
        name=name,
        inputs=[
            InputDefinition(name='input_{}'.format(i)) for i in range(n_inputs)
        ],
        outputs=[
            OutputDefinition(name='output_{}'.format(i))
            for i in range(n_outputs)
        ],
    )
    def solid_fn(info, **_kwargs):
        for i in range(200):
            time.sleep(0.02)
            if i % 1000 == 420:
                info.context.error(
                    'Error message seq={i} from solid {name}'.format(
                        i=i, name=name
                    )
                )
            elif i % 100 == 0:
                info.context.warning(
                    'Warning message seq={i} from solid {name}'.format(
                        i=i, name=name
                    )
                )
            elif i % 10 == 0:
                info.context.info(
                    'Info message seq={i} from solid {name}'.format(
                        i=i, name=name
                    )
                )
            else:
                info.context.debug(
                    'Debug message seq={i} from solid {name}'.format(
                        i=i, name=name
                    )
                )
        return MultipleResults.from_dict(
            {'output_{}'.format(i): 'foo' for i in range(n_outputs)}
        )

    return solid_fn


def define_spew_pipeline():
    return PipelineDefinition(
        name='log_spew',
        solids=[
            nonce_solid('no_in_two_out', 0, 2),
            nonce_solid('one_in_one_out', 1, 1),
            nonce_solid('one_in_two_out', 1, 2),
            nonce_solid('two_in_one_out', 2, 1),
            nonce_solid('one_in_none_out', 1, 0),
        ],
        dependencies={
            SolidInstance('no_in_two_out', alias='solid_a'): {},
            SolidInstance('one_in_one_out', alias='solid_b'): {
                'input_0': DependencyDefinition('solid_a', 'output_0')
            },
            SolidInstance('one_in_two_out', alias='solid_c'): {
                'input_0': DependencyDefinition('solid_a', 'output_1')
            },
            SolidInstance('two_in_one_out', alias='solid_d'): {
                'input_0': DependencyDefinition('solid_b', 'output_0'),
                'input_1': DependencyDefinition('solid_c', 'output_0'),
            },
            SolidInstance('one_in_one_out', alias='solid_e'): {
                'input_0': DependencyDefinition('solid_c', 'output_0')
            },
            SolidInstance('two_in_one_out', alias='solid_f'): {
                'input_0': DependencyDefinition('solid_d', 'output_0'),
                'input_1': DependencyDefinition('solid_e', 'output_0'),
            },
            SolidInstance('one_in_none_out', alias='solid_g'): {
                'input_0': DependencyDefinition('solid_f', 'output_0')
            },
        },
    )
