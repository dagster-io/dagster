import os

from dagster._core.execution.plan.resume_retry import ReexecutionStrategy
from dagster._core.instance.ref import InstanceRef
from dagster._core.storage.tags import MAX_RETRIES_TAG, RETRY_STRATEGY_TAG
from docs_snippets.deploying.job_retries import other_sample_sample_job, sample_job


def test_tags():
    assert sample_job.tags[MAX_RETRIES_TAG] == "3"
    assert other_sample_sample_job.tags[MAX_RETRIES_TAG] == "3"
    assert (
        other_sample_sample_job.tags[RETRY_STRATEGY_TAG]
        == ReexecutionStrategy.ALL_STEPS.value
    )


def test_instance(docs_snippets_folder):
    ref = InstanceRef.from_dir(
        os.path.join(docs_snippets_folder, "deploying", "dagster_instance")
    )

    assert ref.settings["run_retries"]["enabled"] == True
    assert ref.settings["run_retries"]["max_retries"] == 3
