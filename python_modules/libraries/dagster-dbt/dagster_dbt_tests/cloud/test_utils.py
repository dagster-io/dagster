import copy
import json
from pathlib import Path
from typing import Any

import pytest
from dagster import AssetMaterialization
from dagster_dbt.cloud.utils import result_to_events

SAMPLE_RUN_RESULTS = json.loads(
    Path(__file__).parent.joinpath("sample_run_results.json").read_text()
)


def refable_result(status: str) -> dict[str, Any]:
    result = copy.deepcopy(SAMPLE_RUN_RESULTS["results"][0])
    result["status"] = status
    if status != "success":
        # dbt records no timings for a node it never built.
        result["timing"] = []
    return result


def materializations_for(status: str) -> list[AssetMaterialization]:
    return [
        event
        for event in result_to_events(refable_result(status))
        if isinstance(event, AssetMaterialization)
    ]


@pytest.mark.parametrize("status", ["success", "no-op", "reused"])
def test_non_error_statuses_materialize(status: str) -> None:
    """`no-op` (dbt-core 1.10+) and `reused` (dbt-core 1.12+) are terminal, non-error statuses
    meaning dbt did not rebuild the node, so the model should still be materialized.
    """
    materializations = materializations_for(status)

    assert len(materializations) == 1
    assert materializations[0].metadata["Status"].value == status


@pytest.mark.parametrize("status", ["error", "fail", "skipped", "runtime error"])
def test_error_statuses_do_not_materialize(status: str) -> None:
    assert materializations_for(status) == []
