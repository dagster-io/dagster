from solidic.definitions import (Solid, SolidInputDefinition, SolidOutputTypeDefinition)
from solidic.graph import SolidRepo
from solidic.execution import (pipeline_repo, SolidExecutionContext)


def create_test_context():
    return SolidExecutionContext()


def create_dummy_output_def():
    return SolidOutputTypeDefinition(
        name='CUSTOM',
        output_fn=lambda _data, _output_arg_dict: None,
        argument_def_dict={},
    )


def create_input_set_input_def(input_name):
    return SolidInputDefinition(
        input_name,
        input_fn=lambda arg_dict: [{input_name: 'input_set'}],
        argument_def_dict={},
    )


def create_root_success_solid(name):
    input_name = name + '_input'

    def root_transform(**kwargs):
        passed_rows = list(kwargs.values())[0]
        passed_rows.append({name: 'transform_called'})
        return passed_rows

    return Solid(
        name=name,
        inputs=[create_input_set_input_def(input_name)],
        transform_fn=root_transform,
        output_type_defs=[create_dummy_output_def()]
    )


def create_root_transform_failure_solid(name):
    input_name = name + '_input'
    inp = SolidInputDefinition(
        input_name,
        input_fn=lambda arg_dict: [{input_name: 'input_set'}],
        argument_def_dict={},
    )

    def failed_transform(**_kwargs):
        raise Exception('Transform failed')

    return Solid(
        name=name,
        inputs=[inp],
        transform_fn=failed_transform,
        output_type_defs=[create_dummy_output_def()]
    )


import copy


def test_transform_failure_pipeline():
    repo = SolidRepo(solids=[create_root_transform_failure_solid('failing')])
    steps = []
    for step in pipeline_repo(create_test_context(), repo, {'failing_input': {}}):
        steps.append(copy.deepcopy(step))

    assert len(steps) == 1
    assert not steps[0].success
