from dagster._core.definitions.dependency import Node
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.system_config.objects import ResolvedRunConfig
from dagstermill.manager import MANAGER_FOR_NOTEBOOK_INSTANCE

BARE_OUT_OF_JOB_CONTEXT = MANAGER_FOR_NOTEBOOK_INSTANCE.get_context()


def test_tags():
    context = BARE_OUT_OF_JOB_CONTEXT

    assert not context.has_tag("foo")
    assert context.get_tag("foo") is None


def test_run_id():
    assert BARE_OUT_OF_JOB_CONTEXT.run_id is not None
    assert BARE_OUT_OF_JOB_CONTEXT.run.run_id == BARE_OUT_OF_JOB_CONTEXT.run_id


def test_run_config():
    assert BARE_OUT_OF_JOB_CONTEXT.run_config == {"loggers": {"dagstermill": {}}}


def test_logging_tags():
    assert BARE_OUT_OF_JOB_CONTEXT.logging_tags["job_name"] == "ephemeral_dagstermill_pipeline"


def test_environment_config():
    assert isinstance(BARE_OUT_OF_JOB_CONTEXT.resolved_run_config, ResolvedRunConfig)


def test_job_def():
    assert BARE_OUT_OF_JOB_CONTEXT.job_def.name == "ephemeral_dagstermill_pipeline"
    assert len(BARE_OUT_OF_JOB_CONTEXT.job_def.nodes) == 1
    assert BARE_OUT_OF_JOB_CONTEXT.job_def.nodes[0].name == "this_op"


def test_resources():
    assert isinstance(BARE_OUT_OF_JOB_CONTEXT.resources, tuple)


def test_op_def():
    assert isinstance(BARE_OUT_OF_JOB_CONTEXT.op_def, OpDefinition)


def test_node():
    assert isinstance(BARE_OUT_OF_JOB_CONTEXT.node, Node)


def test_log(capsys):
    BARE_OUT_OF_JOB_CONTEXT.log.info("Ho ho!")
    assert "Ho ho!" in capsys.readouterr().err
