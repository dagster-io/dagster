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


def test_construct_full_environment():
    document = '''
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
        materializations=[
            config.Materialization(
                solid='solid_one',
                name='mat_name',
                args={'baaz': 'quux'},
            )
        ],
        context=config.Context('default', {'context_arg': 'context_value'}),
    )
