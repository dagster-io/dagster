from docs_snippets_crag.concepts.configuration.configurable_op import config_example
from docs_snippets_crag.concepts.configuration.configurable_op_with_schema import nests_configurable


def execute_with_config():
    # start_execute_with_config
    result = config_example.execute_in_process(
        run_config={"ops": {"uses_config": {"config": {"iterations": 1}}}}
    )
    # end_execute_with_config
    assert result.success


def execute_with_bad_config():
    # start_execute_with_bad_config
    result = nests_configurable.execute_in_process(
        run_config={
            "ops": {"configurable_with_schema": {"config": {"nonexistent_config_value": 1}}}
        }
    )
    # end_execute_with_bad_config
    assert result.success
