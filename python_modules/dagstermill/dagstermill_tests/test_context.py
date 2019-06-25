import pytest

from dagster.check import CheckError
from dagster.core.system_config.objects import EnvironmentConfig

from dagstermill import MANAGER_FOR_NOTEBOOK_INSTANCE


OUT_OF_PIPELINE_CONTEXT = MANAGER_FOR_NOTEBOOK_INSTANCE.define_out_of_pipeline_context()


def test_tags():
    context = OUT_OF_PIPELINE_CONTEXT

    assert not context.has_tag('foo')
    with pytest.raises(KeyError):
        assert not context.get_tag('foo')


def test_bad_keys():
    with pytest.warns(
        UserWarning,
        match=r'Config keys will not be respected for in-notebook execution: \[\'loggers\'\]',
    ):
        MANAGER_FOR_NOTEBOOK_INSTANCE.define_out_of_pipeline_context({'loggers': {'foo': {}}})


def test_run_id():
    assert OUT_OF_PIPELINE_CONTEXT.run_id is not None


def test_environment_dict():
    assert OUT_OF_PIPELINE_CONTEXT.environment_dict == {
        'execution': {},
        'expectations': {'evaluate': True},
        'loggers': {},
        'resources': {},
        'solids': {},
    }


def test_logging_tags():
    assert OUT_OF_PIPELINE_CONTEXT.logging_tags.get('pipeline') == 'Ephemeral Notebook Pipeline'


def test_environment_config():
    assert isinstance(OUT_OF_PIPELINE_CONTEXT.environment_config, EnvironmentConfig)


def test_pipeline_def():
    assert OUT_OF_PIPELINE_CONTEXT.pipeline_def.name == 'Ephemeral Notebook Pipeline'
    assert OUT_OF_PIPELINE_CONTEXT.pipeline_def.solids == []


def test_resources():
    assert isinstance(OUT_OF_PIPELINE_CONTEXT.resources, tuple)


def test_solid_def():
    with pytest.raises(CheckError):
        _ = OUT_OF_PIPELINE_CONTEXT.solid_def


def test_solid():
    with pytest.raises(CheckError):
        _ = OUT_OF_PIPELINE_CONTEXT.solid


def test_log(capsys):
    OUT_OF_PIPELINE_CONTEXT.log.info('Ho ho!')
    assert 'orig_message = "Ho ho!"\n' in capsys.readouterr().err
