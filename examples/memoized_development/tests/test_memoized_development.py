import tempfile

from memoized_development.repo import my_pipeline
from dagster._core.test_utils import instance_for_test
from dagster._legacy import execute_pipeline


def test_memoized_development():
    with tempfile.TemporaryDirectory() as temp_dir:
        with instance_for_test(temp_dir=temp_dir) as instance:
            result = execute_pipeline(
                my_pipeline,
                run_config={
                    "solids": {
                        "emit_dog": {"config": {"dog_breed": "poodle"}},
                        "emit_tree": {"config": {"tree_species": "weeping_willow"}},
                    },
                    "resources": {"io_manager": {"config": {"base_dir": temp_dir}}},
                },
                instance=instance,
            )
            assert result.success
