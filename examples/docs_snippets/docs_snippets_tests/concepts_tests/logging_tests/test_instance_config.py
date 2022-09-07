from dagster import DagsterInstance
from dagster._core.instance import InstanceRef
from dagster._utils import file_relative_path


def test_valid_managed_loggers_instance_yaml():
    ref = InstanceRef.from_dir(
        base_dir=file_relative_path(__file__, "../../../docs_snippets/concepts/logging"),
        config_filename="python_logging_managed_loggers_config.yaml",
    )
    instance = DagsterInstance.from_ref(ref)
    assert instance.managed_python_loggers == ["my_logger", "my_other_logger"]


def test_valid_log_level_instance_yaml():
    ref = InstanceRef.from_dir(
        base_dir=file_relative_path(__file__, "../../../docs_snippets/concepts/logging"),
        config_filename="python_logging_python_log_level_config.yaml",
    )
    instance = DagsterInstance.from_ref(ref)
    assert instance.python_log_level == "INFO"


def test_valid_handler_instance_yaml():
    ref = InstanceRef.from_dir(
        base_dir=file_relative_path(__file__, "../../../docs_snippets/concepts/logging"),
        config_filename="python_logging_handler_config.yaml",
    )
    instance = DagsterInstance.from_ref(ref)
    assert len(instance.get_handlers()) == 2


def test_valid_file_instance_yaml():
    ref = InstanceRef.from_dir(
        base_dir=file_relative_path(__file__, "../../../docs_snippets/concepts/logging"),
        config_filename="python_logging_file_output_config.yaml",
    )
    instance = DagsterInstance.from_ref(ref)
    assert len(instance.get_handlers()) == 2
