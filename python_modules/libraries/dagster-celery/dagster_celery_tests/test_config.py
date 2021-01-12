import os

from dagster.core.test_utils import environ
from dagster.seven import tempfile
from dagster_celery.cli import get_config_dir

CONFIG_YAML = """
execution:
  celery:
    broker: "pyampqp://foo@bar:1234//"
    config_source:
      foo: "bar"
"""

ENV_CONFIG_YAML = """
execution:
  celery:
    broker:
      env: BROKER_URL
    config_source:
      foo: "bar"
"""


CONFIG_PY = """broker_url = \'pyampqp://foo@bar:1234//\'
result_backend = \'rpc://\'
foo = \'bar\'
"""

CONFIG_PYTHON_FILE = "{config_module_name}.py".format(config_module_name="dagster_celery_config")


def test_config_value_from_yaml():
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(CONFIG_YAML.encode("utf-8"))
        tmp.seek(0)
        python_path = get_config_dir(config_yaml=tmp.name)

    with open(os.path.join(python_path, CONFIG_PYTHON_FILE), "r") as fd:
        assert str(fd.read()) == CONFIG_PY


def test_config_value_from_empty_yaml():
    with tempfile.NamedTemporaryFile() as tmp:
        tmp.write(b"")
        tmp.seek(0)
        python_path = get_config_dir(config_yaml=tmp.name)

    with open(os.path.join(python_path, CONFIG_PYTHON_FILE), "r") as fd:
        assert str(fd.read()) == "result_backend = 'rpc://'\n"


def test_config_value_from_env_yaml():
    with environ({"BROKER_URL": "pyampqp://foo@bar:1234//"}):
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(CONFIG_YAML.encode("utf-8"))
            tmp.seek(0)
            python_path = get_config_dir(config_yaml=tmp.name)

        with open(os.path.join(python_path, CONFIG_PYTHON_FILE), "r") as fd:
            assert str(fd.read()) == CONFIG_PY
