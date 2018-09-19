import sys
import pytest

import papermill as pm

from dagster import (
    execute_pipeline,
    SolidDefinition,
    OutputDefinition,
    PipelineDefinition,
    Result,
)

from dagster.utils import script_relative_path

import dagstermill as dm


def test_basic():
    inputs = dm.define_inputs(a=1)
    assert dm.get_input(inputs, 'a') == 1


def nb_test_path(name):
    return script_relative_path('notebooks/{name}.ipynb'.format(name=name))


def define_hello_world_solid():
    def _transform(_info, _inputs):
        pm.execute_notebook(nb_test_path('hello_world'), '/tmp/out.ipynb', parameters=dict())

    return SolidDefinition(
        name='test',
        inputs=[],
        transform_fn=_transform,
        outputs=[],
        config_def=None,
    )


def define_hello_world_with_output():
    def _transform(info, _inputs):
        pm.execute_notebook(
            nb_test_path('hello_world_output'),
            '/tmp/out.ipynb',
            parameters=dict(),
        )

        nb = pm.read_notebook('/tmp/out.ipynb')
        for output_def in info.solid_def.output_defs:
            if output_def.name in nb.data:
                yield Result(nb.data[output_def.name], output_def.name)

    return SolidDefinition(
        name='test',
        inputs=[],
        transform_fn=_transform,
        outputs=[OutputDefinition()],
        config_def=None,
    )


# Notebooks encode what version of python (e.g. their kernel)
# they run on, so we can't run notebooks in python2 atm
def notebook_test(f):
    return pytest.mark.skipif(
        sys.version_info < (3, 5),
        reason='''Notebooks execute in their own process and hardcode what "kernel" they use.
        All of the development notebooks currently use the python3 "kernel" so they will
        not be executable in a container that only have python2.7 (e.g. in CircleCI)
        ''',
    )(f)


@notebook_test
def test_hello_world():
    pipeline = PipelineDefinition(solids=[define_hello_world_solid()])
    result = execute_pipeline(pipeline)
    assert result.success


@notebook_test
def test_hello_world_with_output():
    pipeline = PipelineDefinition(solids=[define_hello_world_with_output()])
    result = execute_pipeline(pipeline)
    assert result.success
    assert result.result_for_solid('test').transformed_value() == 'hello, world'
