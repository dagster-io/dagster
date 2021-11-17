import tempfile

from bite_sized.conditional_branching import conditional_branching
from dagster.core.test_utils import instance_for_test


def test_conditional_branching():
    with tempfile.TemporaryDirectory() as tmp_dir:
        with instance_for_test(temp_dir=tmp_dir) as instance:
            assert conditional_branching.execute_in_process(
                instance=instance,
                run_config={
                    "ops": {
                        "all_csv": {"config": f"{tmp_dir}/all_articles.csv"},
                        "nyc_csv": {"config": f"{tmp_dir}/nyc_articles.csv"},
                    },
                    "resources": {"slack": {"config": {"token": "nonce"}}},
                },
            ).success
