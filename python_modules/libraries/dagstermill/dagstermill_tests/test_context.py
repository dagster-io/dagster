from dagstermill.manager import MANAGER_FOR_NOTEBOOK_INSTANCE

from dagster import SolidDefinition
from dagster.core.definitions.dependency import Solid
from dagster.core.system_config.objects import EnvironmentConfig

BARE_OUT_OF_PIPELINE_CONTEXT = MANAGER_FOR_NOTEBOOK_INSTANCE.get_context()


def test_tags():
    context = BARE_OUT_OF_PIPELINE_CONTEXT

    assert not context.has_tag("foo")
    assert context.get_tag("foo") is None


def test_run_id():
    assert BARE_OUT_OF_PIPELINE_CONTEXT.run_id is not None
    assert BARE_OUT_OF_PIPELINE_CONTEXT.pipeline_run.run_id == BARE_OUT_OF_PIPELINE_CONTEXT.run_id


def test_run_config():
    assert BARE_OUT_OF_PIPELINE_CONTEXT.run_config == {"loggers": {"dagstermill": {}}}


def test_logging_tags():
    assert BARE_OUT_OF_PIPELINE_CONTEXT.logging_tags["pipeline"] == "ephemeral_dagstermill_pipeline"


def test_environment_config():
    assert isinstance(BARE_OUT_OF_PIPELINE_CONTEXT.environment_config, EnvironmentConfig)


def test_pipeline_def():
    assert BARE_OUT_OF_PIPELINE_CONTEXT.pipeline_def.name == "ephemeral_dagstermill_pipeline"
    assert len(BARE_OUT_OF_PIPELINE_CONTEXT.pipeline_def.solids) == 1
    assert BARE_OUT_OF_PIPELINE_CONTEXT.pipeline_def.solids[0].name == "this_solid"


def test_resources():
    assert isinstance(BARE_OUT_OF_PIPELINE_CONTEXT.resources, tuple)


def test_solid_def():
    assert isinstance(BARE_OUT_OF_PIPELINE_CONTEXT.solid_def, SolidDefinition)


def test_solid():
    assert isinstance(BARE_OUT_OF_PIPELINE_CONTEXT.solid, Solid)


def test_log(capsys):
    BARE_OUT_OF_PIPELINE_CONTEXT.log.info("Ho ho!")
    assert "Ho ho!" in capsys.readouterr().err
