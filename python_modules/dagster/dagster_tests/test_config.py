import pytest
import yaml

from dagster import config


def test_config():
    mat = config.Materialization(solid='some_solid', name='a_mat_type', args={})
    assert isinstance(mat, config.Materialization)
    assert mat.solid == 'some_solid'
    assert mat.name == 'a_mat_type'
    assert mat.args == {}


def test_bad_config():
    with pytest.raises(Exception):
        config.Materialization(solid='name', name=1, args={})


def test_construct_sources_only_environment():
    document = '''
sources:
    solid_one:
        input_one:
            name: some_source
            args:
                foo: bar
'''

    environment = config.construct_environment(yaml.load(document))

    assert environment.sources == {
        'solid_one': {
            'input_one': config.Source(
                name='some_source',
                args={'foo': 'bar'},
            )
        }
    }


def test_construct_full_environment():
    document = '''
sources:
    solid_one:
        input_one:
            name: some_source
            args:
                foo: bar

materializations:
    -   solid: solid_one
        name: mat_name
        args:
            baaz: quux

context:
    name: default
    args:
        context_arg: context_value
'''

    environment = config.construct_environment(yaml.load(document))

    assert environment == config.Environment(
        sources={
            'solid_one': {
                'input_one': config.Source(
                    name='some_source',
                    args={'foo': 'bar'},
                )
            }
        },
        materializations=[
            config.Materialization(
                solid='solid_one',
                name='mat_name',
                args={'baaz': 'quux'},
            )
        ],
        context=config.Context('default', {'context_arg': 'context_value'}),
    )
