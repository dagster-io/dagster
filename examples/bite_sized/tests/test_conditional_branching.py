from dagster import ResourceDefinition
from dagster.core.test_utils import instance_for_test
from bite_sized.conditional_branching import conditional_branching


def test_conditional_branching():
    with instance_for_test() as instance:
        assert conditional_branching.execute_in_process(
            instance=instance,
            run_config={
                "ops": {
                    "all_csv": {"config": "all_articles.csv"},
                    "nyc_csv": {"config": "nyc_articles.csv"},
                },
                "resources": {"slack": {"config": {"token": "nonce"}}},
            },
        ).success
